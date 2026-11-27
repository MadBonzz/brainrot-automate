"""Review the final encoded picture and verify the dialogue in its actual audio stream."""
from array import array
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from html import escape

from . import audio


def movie_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as movie:
        for block in iter(lambda: movie.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def dialogue_check(movie, lines, ffmpeg, assets):
    """Compare the decoded AAC with each intended recording in multiple speech windows."""
    decoded = array("h")
    decoded.frombytes(subprocess.check_output([
        ffmpeg, "-v", "error", "-threads", "1", "-i", str(movie), "-map", "0:a:0",
        "-vn", "-ac", "1", "-ar", str(audio.RATE), "-f", "s16le", "-"
    ]))
    if sys.byteorder != "little":
        decoded.byteswap()
    rows = []
    for line in lines:
        ref, _ = audio.narration(line["say"], movie.parent, ffmpeg, assets)
        at = round(line["speech_start"] * audio.RATE)
        if at + len(ref) > len(decoded):
            raise ValueError(f"Missing end of dialogue at {line['id']}")
        scores = []
        window = audio.RATE // 2
        for first in range(0, len(ref), window):
            stop = min(first + window, len(ref))
            x = ref[first:stop:12]
            y = decoded[at + first:at + stop:12]
            xx = sum(v*v for v in x)
            if xx < max(len(x), 1)*35**2:
                continue
            yy = sum(v*v for v in y)
            xy = sum(v*w for v,w in zip(x,y))
            scores.append(xy / math.sqrt(xx * yy) if yy else 0.)
        if not scores or min(scores) < .80:
            raise ValueError(f"Exported speech differs from the recording at {line['id']}")
        rows.append({"id":line["id"],"windows":len(scores),"lowest_correlation":round(min(scores),4)})
    return rows


def review_page(movie, manifest):
    """Make a standalone cue player. Reviewer observations apply only to this encode."""
    manifest = dict(manifest)
    manifest["sha256"] = movie_hash(movie)
    data = json.dumps(manifest,ensure_ascii=False).replace("<","\\u003c")
    template = """<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Screening room</title><style>
*{box-sizing:border-box}body{margin:0;background:#141923;color:#f4efe5;font:16px system-ui}
main{display:grid;grid-template-columns:minmax(240px,42%) 1fr;gap:24px;padding:20px;max-width:1300px;margin:auto}
video{width:100%;height:80vh;object-fit:contain;background:#080b10;position:sticky;top:12px}
button,select,textarea{font:inherit;padding:6px}article{border-top:1px solid #516071;padding:14px 0}p{margin:.5em 0}
small{color:#bbcad4}textarea{width:100%;min-height:40px;margin-top:8px}
@media(max-width:700px){main{display:block}video{height:42vh}}
</style><main><video src="__SOURCE__" controls playsinline></video><section><h1></h1>
<p>Play the film with sound, then revisit each line. Record what the camera actually shows.</p>
<button id="save">Export screening notes</button><div id="rows"></div></section></main>
<script>
const film=__DATA__, v=document.querySelector('video'), rows=document.querySelector('#rows');
document.querySelector('h1').textContent=film.title;
let end=null,notes={};try{notes=JSON.parse(localStorage.getItem(film.sha256)||'{}')}catch{}
function remember(){try{localStorage.setItem(film.sha256,JSON.stringify(notes))}catch{}}
v.ontimeupdate=()=>{if(end!==null && v.currentTime>=end){end=null;v.pause()}};
function el(tag,value,parent){const n=document.createElement(tag);n.textContent=value;parent.appendChild(n);return n}
for(const line of film.lines){
 const n=el('article','',rows),b=el('button','▶ '+line.start.toFixed(1)+'–'+line.end.toFixed(1)+' s',n);
 b.onclick=()=>{end=line.end;v.currentTime=line.start;v.play()};
 el('p',line.say,n);el('small','Look for '+line.evidence,n);
 const p=el('p','',n),s=el('select','',p);
 for(const opt of ['Unreviewed','Visible','Needs revision'])el('option',opt,s);
 const t=el('textarea','',n);t.placeholder='What did you see and hear?';
 s.value=notes[line.id]?.status||'Unreviewed';t.value=notes[line.id]?.note||'';
 const store=()=>{notes[line.id]={status:s.value,note:t.value};remember()};
 s.onchange=store;t.oninput=store;
}
document.querySelector('#save').onclick=()=>{
 const file=new Blob([JSON.stringify({title:film.title,sha256:film.sha256,notes},null,2)],{type:'application/json'});
 const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download='visual-review.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),3000)};
</script>"""
    html = template.replace("__SOURCE__",escape(movie.name,quote=True)).replace("__DATA__",data)
    (movie.parent/"screening.html").write_text(html,encoding="utf8")


def inspect(movie, assets=None, ffmpeg="ffmpeg"):
    import shutil
    ffmpeg=shutil.which(ffmpeg) or ffmpeg
    info=json.loads((movie.parent/"screening.json").read_text(encoding="utf8"))
    checks=dialogue_check(movie,info["lines"],ffmpeg,assets)
    data={"sha256":movie_hash(movie),"dialogue":checks}
    (movie.parent/"audio-checks.json").write_text(json.dumps(data,indent=2),encoding="utf8")
    review_page(movie,info)
    return data


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("movie",type=Path)
    parser.add_argument("--assets",type=Path)
    args=parser.parse_args()
    inspect(args.movie.resolve(),args.assets)
