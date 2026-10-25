# G. Siddarth ♥ S. Kowsalya — Wedding Invitation

A traditional, animated wedding invitation website (mobile and desktop) plus a WhatsApp-ready invitation video.

- **Wedding (Muhurtham):** Monday, 16 November 2026, 6:00–7:30 AM
- **Reception:** Sunday, 15 November 2026, 6:30 PM onwards
- **Venue:** Manjula Mahal A/C Thirumana Mandapam, Poonamallee – Avadi High Road, Opp. Vivekanandha School, Avadi, Chennai

## What's inside
- `index.html` — the website. Carved temple doors open on tap, jasmine garlands and brass bells sway, a temple arch draws itself around the names, jasmine and rose petals fall, a kuthuvilakku glows. Sections: blessings, parents, the couple, a tap-to-open invitation envelope, reception and wedding (with calendar buttons), countdown, venue with map and directions, and the closing message. Music ("Marriage at 2AM" theme from *Vikram*, `assets/music.mp3`) plays after opening and can be muted.
- `assets/invitation.mp4` — 47-second vertical (720×1280) invitation video with the same music, about 5 MB, to send directly on WhatsApp or post as a status.
- `og.jpg` — the preview image WhatsApp shows when the link is shared.

## Personalised links
Add `?to=Name` to greet a guest by name on the opening screen, for example
`https://<your-site>.vercel.app/?to=Ravi%20Family`

## Hosting
Deployed on Vercel from the `main` branch (no build step; Framework Preset: Other). Every push to `main` goes live automatically.

## Rebuilding the video
`video-src/` holds the scene (`video.html`), the frame renderer (`render.js`, Playwright), an optional synthesised soundtrack (`music.py`, not used in the current video) and the script that cut the decorative assets from the design (`extract_assets.py`).

```sh
node video-src/render.js /tmp/frames 30
python3 video-src/music.py /tmp/music.wav 47
ffmpeg -framerate 30 -i /tmp/frames/%05d.jpg -i /tmp/music.wav -c:v libx264 -crf 24 -pix_fmt yuv420p \
  -c:a aac -b:a 128k -shortest -movflags +faststart assets/invitation.mp4
```
