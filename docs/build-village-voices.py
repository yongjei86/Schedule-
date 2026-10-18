"""Build bundled Korean dialogue from public character names and generic greetings.

No child/family names are sent to the speech service. Playback has no TTS dependency.
Requires edge-tts and ffmpeg. Run from the repository root.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import asyncio
import os
import subprocess
import edge_tts
import edge_tts.communicate

# Honor the execution environment's configured CA without disabling verification.
if os.environ.get('SSL_CERT_FILE'):
 edge_tts.communicate._SSL_CTX.load_verify_locations(cafile=os.environ['SSL_CERT_FILE'])

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'static' / 'dressup' / 'voices-v2'
LINES = {
 'chacha': '안녕! 나는 차차핑이야. 우리 같이 꽃밭을 산책할까?',
 'shasha': '안녕! 나는 샤샤핑이야. 골라 준 옷이 정말 마음에 들어!',
 'saekom': '안녕! 나는 새콤핑이야. 오늘은 어떤 재미있는 놀이를 해 볼까?',
 'banjjak': '안녕! 나는 반짝핑이야. 만나서 반짝반짝 기분이 좋아!',
 'hachoo': '안녕! 나는 하츄핑이야. 사랑해! 우리 같이 놀자!',
 'yeou': '안녕! 나는 여우핑이야. 마을에 놀러 와 줘서 고마워!',
 'kkang': '안녕! 나는 깡총핑이야. 우리 같이 깡충깡충 뛰어 볼까?',
 'ballet': '안녕! 나는 발레핑이야. 나랑 예쁘게 춤춰 볼까?',
 'yogu': '안녕! 나는 요거핑이야. 같이 산책하니까 정말 즐거워!',
 'pudding': '안녕! 나는 푸딩핑이야. 달콤한 하루야! 오늘 기분이 어때?',
 'dalkom': '안녕! 나는 달콤핑이야. 오늘도 만나서 정말 반가워!',
 'eclipse': '안녕! 나는 이클립스핑이야. 반짝이는 보석처럼 멋진 하루를 보내자!',
 'your-day': '안녕! 오늘 재미있었던 일을 들려줄래? 나는 네 이야기가 듣고 싶어.',
 'see-you': '오늘도 함께 놀아서 즐거웠어. 다음에도 우리 마을에 놀러 와 줘!',
}

PROFILES = {key: (rate, pitch) for key, rate, pitch in [('chacha','+8%','+22Hz'),('shasha','+3%','+15Hz'),('saekom','+12%','+30Hz'),('banjjak','+14%','+35Hz'),('hachoo','+7%','+32Hz'),('yeou','+4%','+20Hz'),('kkang','+16%','+38Hz'),('ballet','+2%','+24Hz'),('yogu','+6%','+18Hz'),('pudding','+3%','+26Hz'),('dalkom','+8%','+28Hz'),('eclipse','-3%','+10Hz')]}
JOBS = {f'{key}-{turn}': (key, text) for key in PROFILES for turn, text in enumerate([LINES[key],LINES['your-day'],LINES['see-you']])}

def build(item):
 key, (character, text) = item
 rate, pitch = PROFILES[character]
 target = OUT / (key + '.mp3')
 if target.exists() and target.stat().st_size > 1000:
  return key
 temporary = OUT / (key + '.raw.mp3')
 asyncio.run(edge_tts.Communicate(text, 'ko-KR-SunHiNeural', rate=rate, pitch=pitch).save(str(temporary)))
 subprocess.run(['ffmpeg', '-nostdin', '-loglevel', 'error', '-y', '-i', str(temporary),
                 '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '24000',
                 '-ac', '1', '-b:a', '48k', str(target)], check=True)
 temporary.unlink()
 return key

if __name__ == '__main__':
 OUT.mkdir(parents=True, exist_ok=True)
 with ThreadPoolExecutor(max_workers=3) as pool:
  for name in pool.map(build, JOBS.items()):
   print('Built', name, flush=True)
 (OUT / 'dialogue.json').write_text(json.dumps(LINES, ensure_ascii=False, indent=2) + '\n')
