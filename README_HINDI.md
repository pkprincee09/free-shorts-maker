# Free Shorts Maker — mobile setup starter

## Ye version kya karta hai?
- Mobile se video upload **ya** YouTube URL input
- Video ko 15, 30, 45 ya 60 second ke clips mein kaatna
- Sab clips ZIP mein download karna

**Abhi AI highlights, automatic Hindi captions, aur 9:16 smart crop included nahi hain.** Yeh pehla working starter hai.

## Mobile se free deploy (GitHub + Render)
1. GitHub par sign in karein aur naya repository banayein, naam `free-shorts-maker`.
2. Is ZIP ko extract karke saari files repository ke root mein upload karein. `templates/index.html` ko isi folder structure mein rakhein.
3. Render.com par sign in karein, **New + → Blueprint** choose karein aur GitHub repository connect karein.
4. Render `render.yaml` se service banayega. Deploy complete hone par Render ka URL kholein.
5. Android Chrome se video upload karein ya YouTube URL paste karein.

## Zaroori baatein
- Free cloud services sleep/limits kar sakti hain; large videos time out ho sakte hain.
- YouTube URL processing har video par kaam nahi karegi. Private, age-restricted, region-blocked, members-only, or unsupported videos fail ho sakte hain.
- Sirf apne videos ya jinke liye permission hai unhein process karein; YouTube ki terms aur copyright ka dhyan rakhein.
- Video temporary server storage par aata hai. Is starter ko sensitive videos ke liye use na karein.
- Production se pehle rate limiting, automatic cleanup, authentication, and security review add karein.
- This project does not promise fully AI-generated highlights or captions; those require additional models/integration.
