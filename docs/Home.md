# MenuSync AI

Turns a restaurant menu image into category, item and price rows with EasyOCR plus spatial line grouping, with a batch engine that writes JSON and CSV and scores itself against ground truth. Portfolio, Computer Vision, by Maximus Friedrich Baluyot.

**Watch first:** [the 90-second film](https://github.com/Keshigami/headstorm_menu/blob/main/demo/film.mp4).

## Pages
- [Getting started](Getting-Started.md): run it in three commands, what you see, the API.
- [How it was built](How-It-Was-Built.md): from the brief to a running service, step by step.
- [Results](Results.md): the numbers and what they mean.
- [Limits and next steps](Limits-and-Next-Steps.md): what it cannot do yet.
- [The film](The-Film.md): what the four chapters show.

## The brief
A hospitality-tech client wants competitor pricing across more than a thousand restaurants, and the menus arrive as
images. Typing them in does not scale. This pipeline reads a menu image and returns structured rows (restaurant,
category, item, price) plus an annotated picture, and a batch engine does the same over a folder with an error log
for the unreadable ones. "Solved" means a CSV a pricing analyst can load, with a measured accuracy next to it.

## The one-line answer
100% · items and prices · 71 items · 5 synthetic menus

## One honest limit
Synthetic menus only. Photos will score lower.
