"""Render a vertical Nubi TikTok video from a JSON spec.

Usage:  python3 kit/make_video.py spec.json videos/AAAA-MM-DD-tema.mp4
Also writes <output>.jpg (cover) and <output>-revision.jpg (contact sheet to check the frames).

Spec format (all text in Spanish):
{
  "seed": 12,                                # any integer; changes music + decoration
  "hook": ["¿Te sobró", "arroz de ayer?"],    # 1-3 short lines, last one is green
  "hook_sub": "Conviértelo en algo increíble", # optional
  "emojis": ["🍚","🍳","🥚","🧅","🌶️","🍋"], # 4-8 emojis floating in the hook
  "kicker": "RECETA PERUANA",                 # small label above the title
  "dish_emoji": "🍚",
  "title": "Arroz chaufa casero",
  "subtitle": "Listo en 20 minutos",          # optional
  "meta": ["⏱ 20 min", "👥 2 personas", "⭐ Fácil"],   # up to 3 pills
  "steps_label": "PASO",                      # or "TRUCO", "TIP"
  "steps": [ {"emoji":"🥚","text":"Bate 2 huevos y haz una tortilla fina","note":"Córtala en tiras"}, ... ],  # 3-6 steps, text <= 60 chars
  "nubi_says": "¡El secreto es el wok bien caliente!",
  "xp": 150,
  "reward_title": "Cocínalo en Nubi",
  "reward_text": "Sigue los pasos, toma la foto de tu plato y sube de nivel como chef",
  "cta": "👉 Pruébala gratis · link en la bio"
}
"""
import json, os, sys, subprocess, tempfile, shutil
from playwright.sync_api import sync_playwright
KIT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, KIT)
from music import make_music

def main(spec_path, out_mp4, fps=30):
    spec = json.load(open(spec_path, encoding='utf-8'))
    os.makedirs(os.path.dirname(os.path.abspath(out_mp4)), exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='nubi_')
    frames = os.path.join(tmp, 'frames'); os.makedirs(frames)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.add_init_script('window.SPEC=' + json.dumps(spec, ensure_ascii=False) + ';')
        pg.goto('file://' + os.path.join(KIT, 'template.html')); pg.wait_for_timeout(1500)
        if errs: raise SystemExit('Error en la plantilla: ' + errs[0])
        dur = pg.evaluate('window.DURATION'); timeline = pg.evaluate('window.TIMELINE')
        n = int(dur * fps)
        for i in range(n):
            pg.evaluate(f'seek({i / fps})'); pg.screenshot(path=os.path.join(frames, f'f{i:05d}.jpg'), type='jpeg', quality=93)
        b.close()
    wav = make_music(dur, timeline, seed=int(spec.get('seed', 1)), out_path=os.path.join(tmp, 'music.wav'))
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-framerate', str(fps), '-i', os.path.join(frames, 'f%05d.jpg'), '-i', wav,
                    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-r', str(fps),
                    '-c:a', 'aac', '-b:a', '192k', '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-movflags', '+faststart', '-shortest', out_mp4], check=True)
    # cover = title scene; contact sheet for review
    from PIL import Image
    title_frame = int((timeline['cuts'][0] + 1.6) * fps)
    shutil.copy(os.path.join(frames, f'f{min(title_frame, n - 1):05d}.jpg'), out_mp4[:-4] + '.jpg')
    picks = [int(n * k / 12) for k in range(1, 12)] + [n - 15]
    ims = [Image.open(os.path.join(frames, f'f{i:05d}.jpg')).resize((270, 480)) for i in picks]
    sheet = Image.new('RGB', (280 * 6, 490 * 2), 'white')
    for k, im in enumerate(ims): sheet.paste(im, ((k % 6) * 280, (k // 6) * 490))
    sheet.save(out_mp4[:-4] + '-revision.jpg', quality=80)
    shutil.rmtree(tmp)
    print(json.dumps({'video': out_mp4, 'duracion_s': round(dur, 1), 'portada': out_mp4[:-4] + '.jpg', 'revision': out_mp4[:-4] + '-revision.jpg'}, ensure_ascii=False))

if __name__ == '__main__':
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
