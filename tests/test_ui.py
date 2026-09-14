"""Optional browser acceptance. Set KAJAMITE_BROWSER to an existing Chromium."""
import html as html_module
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from kajamite import receipt
from kajamite.ui import html


@unittest.skipUnless(os.environ.get('KAJAMITE_BROWSER'), 'set KAJAMITE_BROWSER for browser acceptance')
class UiTests(unittest.TestCase):
    def test_disclosure_and_host_states(self):
        before = {'file_path': 'Notes/Example.md', 'content': 'old', 'metadata': {}}
        change = receipt.for_revise(before, before | {'content': 'new'}, [
            {'find_text': f'old passage {i}', 'replacement': f'new passage {i}'} for i in range(9)])
        unchanged = receipt.for_revise(before, before, [{'find_text': 'old', 'replacement': 'old'}])
        script = r'''
const frame = document.querySelector('iframe');
let requests = [], modeReply = 'fullscreen', sizes = 0, initialized;
const initialization = new Promise(resolve => initialized = resolve);
const reply = data => frame.contentWindow.postMessage({jsonrpc:'2.0', ...data}, '*');
window.addEventListener('message', e => {
 if (e.source !== frame.contentWindow) return;
 const m = e.data;
 if (m.method === 'ui/initialize') reply({id:m.id,result:{hostContext:{displayMode:'inline',availableDisplayModes:['inline','fullscreen']}}});
 if (m.method === 'ui/notifications/initialized') initialized();
 if (m.method === 'ui/request-display-mode') {
  requests.push(m.params.mode);
  if (modeReply === 'reject') reply({id:m.id,error:{code:-32000,message:'Unavailable'}});
  else if (modeReply !== 'timeout') reply({id:m.id,result:{mode:m.params.mode === 'inline' ? 'inline' : modeReply}});
 }
 if (m.method === 'ui/notifications/size-changed') sizes++;
});
const wait = (ms=40) => new Promise(resolve => setTimeout(resolve,ms));
const doc = () => frame.contentDocument, el = id => doc().getElementById(id);
const assert = (value, label) => { if (!value) throw Error(label); };
const result = async (value, error=false) => {reply({method:'ui/notifications/tool-result',params:{structuredContent:value,isError:error}}); await wait();};
(async () => {
 await initialization; await result({knowledge_change:CHANGE});
 assert(el('review').hidden && !el('evidence').open, 'details start hidden');
 assert(doc().body.getBoundingClientRect().height < 240, 'compact initial height');
 assert(el('counts').textContent === '1 note · 9 changes', 'notes and passages are distinct');
 el('toggle').click(); await wait();
 assert(requests[0] === 'fullscreen' && !el('review').hidden, 'advertised fullscreen');
 assert(el('changes').children.length === 3, 'bounded first disclosure');
 el('more').click(); assert(el('changes').children.length === 6, 'show more');
 reply({method:'ui/notifications/host-context-changed',params:{displayMode:'inline'}}); await wait();
 assert(el('review').hidden, 'host close restores summary');
 for (const mode of ['reject','inline','timeout']) {
  await result({knowledge_change:CHANGE}); modeReply = mode; el('toggle').click(); await wait(mode==='timeout'?1600:40);
  assert(!el('review').hidden, 'inline fallback: '+mode);
 }
 const count = requests.length;
 reply({method:'ui/notifications/host-context-changed',params:{availableDisplayModes:['inline']}}); await wait();
 await result({knowledge_change:CHANGE}); el('toggle').click(); await wait();
 assert(requests.length === count && sizes > 0, 'capability detection and sizing');
 await result({preview:true,identifier:'Notes/Example.md',proposed_content:'Preview text'});
 assert(el('headline').textContent === 'Preview · nothing saved', 'preview');
 await result({knowledge_change:UNCHANGED});
 assert(el('headline').textContent === 'No content changes' && el('counts').textContent.includes('0 changes'), 'no-op');
 await result({replayed:true,knowledge_change:CHANGE});
 assert(el('headline').textContent === 'Previously completed', 'replay');
 await result({completed:[{knowledge_change:CHANGE},{knowledge_change:CHANGE,replayed:true}],errors:[{record_id:'Failed',error:'Uncertain'}],partial:true});
 assert(el('headline').textContent.includes('partially') && el('counts').textContent.startsWith('1 note changed'), 'partial maintenance excludes replay');
 await result({completed:[],errors:[],partial:false});
 assert(el('headline').textContent === 'No new changes', 'empty maintenance');
 await result({content:[{type:'text',text:'uncertain'}]},true);
 assert(el('headline').textContent === 'Operation failed' && el('status').textContent.includes('may have committed'), 'failure');
 await result({}); assert(el('headline').textContent === 'No change receipt returned', 'missing receipt');
 const malicious = JSON.parse(JSON.stringify(CHANGE));
 malicious.after.identifier = '<img src=x onerror="window.pwned=true">';
 malicious.body_change.replacements[0].after.preview = '<script>window.pwned=true<\/script>';
 await result({knowledge_change:malicious}); el('toggle').click(); await wait();
 assert(!doc().querySelector('img') && !frame.contentWindow.pwned, 'inert source text');
 frame.style.width = '320px'; await wait();
 assert(doc().documentElement.scrollWidth <= 320, 'narrow layout');
 reply({method:'ui/notifications/tool-input',params:{}}); await wait();
 assert(el('headline').textContent === 'Working' && el('review').hidden && el('actions').hidden, 'new input clears success');
 reply({method:'ui/notifications/tool-cancelled',params:{reason:'Stopped'}}); await wait();
 assert(el('headline').textContent === 'Operation cancelled', 'cancelled');
 await result({knowledge_change:CHANGE});
 document.getElementById('outcome').textContent = 'BROWSER_ACCEPTANCE_OK';
})().catch(error => document.getElementById('outcome').textContent = 'FAILED: '+error.message);
'''
        script = 'const CHANGE = ' + json.dumps(change) + '; const UNCHANGED = ' + json.dumps(unchanged) + ';\n' + script
        script += '\nframe.srcdoc = ' + json.dumps(html()) + ';'
        with tempfile.TemporaryDirectory(prefix='kajamite-ui-') as directory:
            page = Path(directory) / 'host.html'
            page.write_text('<!doctype html><meta charset="utf-8"><iframe style="width:640px;height:800px"></iframe>'
                            '<pre id="outcome">RUNNING</pre><script>' + script.replace('</script', '<\\/script') + '</script>', encoding='utf-8')
            completed = subprocess.run([
                os.environ['KAJAMITE_BROWSER'], '--headless', '--no-sandbox', '--disable-gpu',
                '--disable-dev-shm-usage', '--no-proxy-server', '--no-first-run',
                '--user-data-dir=' + str(Path(directory) / 'profile'),
                '--virtual-time-budget=9000', '--dump-dom', page.as_uri(),
            ], capture_output=True, text=True, timeout=45)
            self.assertEqual(0, completed.returncode, completed.stderr[-1000:])
            outcome = completed.stdout.split('<pre id="outcome">', 1)[-1].split('</pre>', 1)[0]
            self.assertEqual('BROWSER_ACCEPTANCE_OK', html_module.unescape(outcome))
