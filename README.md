# paul-robineau.github.io

Personal website of Paul Robineau – researcher across nanoscience, sustainability
(Life-Cycle Assessment) and participative action research. Live at
<https://paul-robineau.github.io>.

A small, deliberately low-tech static site. Its purpose and most of its content have not
changed much since the first version (originally built by Nicolas Burger in 2019); the
current version is a lighter, more accessible rebuild of the same idea.

## Design choices

- **Static and self-contained.** Plain HTML and one hand-written `styles.css`. No framework,
  no build step for visitors, no CDN. Open `index.html` and it works offline.
- **Lightweight and private (ecological goal).** No web fonts (the OS UI font is used), no
  icon font (inline SVG), no third-party requests, no analytics, no tracking, no advertising
  cookies. The only script is a first-party one (`theme.js`): a light/dark/auto theme toggle
  (preference kept in `localStorage`, never sent anywhere) and the per-post reading-time.
- **Robust by default.** A Content-Security-Policy on every page, automatic dark mode
  (`prefers-color-scheme`) with a manual override, a responsive layout, and accessibility
  (skip link, focus-visible outlines, alt text, reduced-motion support).
- **Auto-updating publications.** The list on `academic.html` is regenerated at build time
  from HAL, ORCID and Crossref, so it stays current without hand-editing the bulk of it (see
  below). What visitors download is still 100 % static HTML.

## Structure

```
index / phd / academic / associative / legal / 404  .html   the pages
blog/              blog index + one HTML file per post
styles.css         the single stylesheet (system fonts, light + dark)
theme.js           the only script (light/dark/auto theme toggle + post reading-time)
img/  doc/         images, and the PDFs referenced by the pages
tools/             publications generator and its data
.github/workflows/ weekly publications refresh
robots.txt  sitemap.xml  .nojekyll
```

## Publications

`tools/build_publications.py` (Python standard library only, runs at build time) produces
one list per type, each entry tagged by where it comes from:

- **HAL/ORCID** – pulled automatically: HAL → ORCID (DOI'd works HAL lacks) → Crossref (for
  the DOIs listed in `extra_dois`), deduplicated by DOI.
- **Manually added** – hand-kept items in `tools/manual_publications.json` (talks, posters,
  reports, in-preparation, software). When one later appears in HAL/ORCID, delete it from the
  JSON and it reappears automatically tagged HAL/ORCID.

To maintain the list, edit:
- `tools/manual_publications.json` – your hand-kept entries and the `extra_dois` list;
- `tools/featured.json` – which papers show as "Featured" cards (by DOI + image).

The GitHub Action `.github/workflows/update-publications.yml` regenerates `academic.html`
weekly, on demand, and whenever those files change. Run it locally with
`python3 tools/build_publications.py` (add `--check` to see whether it *would* change
anything). It needs no `pip install`.

## Blog

`blog/index.html` is a reverse-chronological list; each post is its own HTML file in `blog/`
(e.g. `blog/a-place-to-think-out-loud.html`). To add an entry: copy an existing post file,
set its `<title>`, `<time datetime="YYYY-MM-DD">` (back-dating is fine) and content, then add a
matching `<li>` card to `blog/index.html` in date order. Reading time is computed in the
browser by `theme.js` (it counts the words in `.post__body`); the index cards show the date
only. Blog pages use root-absolute paths (`/styles.css`, `/index.html`, …) because they live
in a subfolder.

## Local preview

Open `index.html` directly, or serve the folder:

```
python3 -m http.server
```

## Credits

Original site structure by [Nicolas Burger](https://github.com/burgerni10); content and
current design by [Paul Robineau](https://github.com/Paul-Robineau).
