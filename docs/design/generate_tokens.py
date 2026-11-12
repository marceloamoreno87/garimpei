"""Export the single token source. Run with --check to detect drift and bad contrast."""
from pathlib import Path
import argparse
import json
import re

ROOT = Path(__file__).resolve().parent


def resolve(value, palette):
    match = re.fullmatch(r"\{([\w-]+)\}", value)
    return palette[match.group(1)] if match else value


def luminance(color):
    channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [channel / 12.92 if channel <= 0.04045 else ((channel + .055) / 1.055) ** 2.4 for channel in channels]
    return sum(channel * weight for channel, weight in zip(linear, (.2126, .7152, .0722)))


def contrast(foreground, background):
    values = sorted((luminance(foreground), luminance(background)))
    return (values[1] + .05) / (values[0] + .05)


def render(data):
    palette = data['primitives']
    lines = ['/* Generated from tokens.json. Edit the source, then run generate_tokens.py. */', ':root {']
    lines.extend(f'  --p-{name}: {value};' for name, value in palette.items())
    for name, value in data['tokens'].items():
        lines.append(f'  --{name}: {resolve(value, palette)};')
    lines.append('}')
    for name, values in data['themes'].items():
        if not values:
            continue
        lines.append(f'[data-variant="{name}"] {{')
        lines.extend(f'  --{key}: {resolve(value, palette)};' for key, value in values.items())
        lines.append('}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / 'tokens.json').read_text())
    outputs = {ROOT / 'tokens.css': render(data)}
    for name in ['components/components.css', 'prototypes/prototype.css']:
        template = (ROOT / (name + '.in')).read_text()
        compiled = re.sub(r'\{\{([\w-]+)\}\}', lambda match: data['tokens'][match.group(1)], template)
        outputs[ROOT / name] = '/* Generated from ' + Path(name).name + '.in and tokens.json. */\n' + compiled
    for target, generated in outputs.items():
        if args.check:
            if not target.exists() or target.read_text() != generated:
                raise SystemExit(f'{target.relative_to(ROOT)} diverge da fonte. Execute generate_tokens.py.')
        else:
            target.write_text(generated)
    pairs = [('color-text', 'color-bg'), ('color-muted', 'color-bg'), ('color-muted', 'color-surface'), ('color-muted', 'color-raised'), ('color-on-primary', 'color-primary'), ('color-accent-text', 'color-accent-soft'), ('color-warning', 'color-warning-bg'), ('color-danger', 'color-danger-bg'), ('color-info', 'color-info-bg')]
    for theme, overrides in data['themes'].items():
        tokens = {**data['tokens'], **overrides}
        ratios = [contrast(resolve(tokens[front], data['primitives']), resolve(tokens[back], data['primitives'])) for front, back in pairs]
        if min(ratios) < 4.5:
            raise SystemExit(f'Contraste de texto insuficiente em {theme}: {min(ratios):.2f}:1')
        control_ratio = contrast(resolve(tokens['color-control'], data['primitives']), resolve(tokens['color-surface'], data['primitives']))
        if control_ratio < 3:
            raise SystemExit(f'Contraste de borda de controle insuficiente em {theme}: {control_ratio:.2f}:1')
        print(f'{theme}: CSS sincronizado; texto >= {min(ratios):.2f}:1; borda de controle {control_ratio:.2f}:1')


if __name__ == '__main__':
    main()
