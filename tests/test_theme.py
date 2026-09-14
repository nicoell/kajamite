import json
from pathlib import Path
import tempfile
import unittest

from kajamite.config import Settings
from kajamite.theme import load_theme, parse_theme_css, validate_theme
from kajamite.ui import html, resource_uri, RESOURCE_URI


class ThemeTests(unittest.TestCase):
    def test_css_export_and_registry_json_produce_same_theme(self):
        css = '''/* Exported variables */
        :root { --primary: oklch(0.6 0.15 250); --font-sans: "Example", sans-serif; --radius: 0.5rem; }
        .dark { --primary: oklch(0.8 0.1 250); }
        @theme inline { --color-primary: var(--primary); }
        '''
        theme = parse_theme_css(css)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'theme.css').write_text(css)
            (root/'theme.json').write_text(json.dumps({'name':'example','cssVars':{'theme':{'font-sans':'\"Example\", sans-serif'}, **theme}}))
            self.assertEqual(theme, load_theme(root/'theme.css'))
            self.assertEqual(validate_theme({'theme':{'font-sans':'\"Example\", sans-serif'}, **theme}), load_theme(root/'theme.json'))
            (root/'theme.json').write_text(json.dumps(theme))
            self.assertEqual(theme, load_theme(root/'theme.json'))
        self.assertEqual('"Example", sans-serif', theme['light']['font-sans'])

    def test_invalid_theme_data_never_becomes_styles_or_code(self):
        for value in ['red; color: blue', '</script><script>alert(1)</script>', 'url(https://example.com/font)',
                      'u\\72l(example)', 'image-set("https://example.com")', 'red !important;', '/*x*/ red', 'red\nblue']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_theme({'light':{'primary':value}})
        for value in [{'unexpected':{}}, {'light':[]}, {'light':{'unknown':'red'}}, {'light':{'primary':2}},
                      {'light':{'primary':'x'*513}}, {'light':{'primary':'red','--primary':'blue'}}]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_theme(value)
        for value in ['@import "x"; :root {--primary:red;}', 'body {background:red}', ':root {color:red}',
                      ':root {--primary:red;--primary:blue}', ':root {--unknown:red}', 'broken']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_theme_css(value)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'theme.css';path.write_text(' '*32769)
            with self.assertRaises(ValueError): load_theme(path)

    def test_configuration_resolves_theme_relative_to_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'config.toml'
            base='[backend]\ncommand="backend"\nproject="example"\n'
            path.write_text(base+'[ui]\ntheme="theme.css"\n')
            self.assertEqual(path.parent/'theme.css',Settings.load(path).ui_theme)
            for tail in ['[ui]\ntheme=7','[ui]\ntheme=""','[ui]\nunknown="theme.css"']:
                path.write_text(base+tail)
                with self.assertRaises(ValueError): Settings.load(path)
            path.write_text(base)
            self.assertIsNone(Settings.load(path).ui_theme)

    def test_theme_does_not_change_bundle_and_has_its_own_cache_key(self):
        theme={'light':{'primary':'#123456'}}
        themed=html(theme);plain=html()
        self.assertNotIn('__KAJAMITE_THEME_JSON__',themed)
        def without_theme(text):
            start=text.index('<script id="kajamite-theme"')
            end=text.index('</script>',start)
            return text[:start]+text[end:]
        self.assertEqual(without_theme(plain),without_theme(themed))
        self.assertEqual(RESOURCE_URI,resource_uri())
        self.assertNotEqual(RESOURCE_URI,resource_uri(theme))
        self.assertNotEqual(resource_uri(theme),resource_uri({'light':{'primary':'#654321'}}))
        self.assertEqual(resource_uri(theme),resource_uri({'light':{'--primary':'#123456'},'dark':{}}))

    def test_tweakcn_common_typography_and_shadow_export(self):
        exported = {'theme': {'font-sans':'Arial, sans-serif', 'tracking-tight':'calc(var(--tracking-normal) - 0.025em)'},
                    'light': {'primary':'oklch(0.6 0.15 250)', 'tracking-normal':'0em', 'letter-spacing':'0em',
                              'shadow-sm':'0px 1px 3px 0px hsl(0 0% 0% / 0.1)'},
                    'dark': {'letter-spacing':'0.02em'}}
        actual = validate_theme(exported)
        self.assertEqual('Arial, sans-serif',actual['light']['font-sans'])
        self.assertEqual('0.02em',actual['dark']['tracking-normal'])
        self.assertNotIn('theme',actual)
