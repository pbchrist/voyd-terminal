# The Fourth Bell

**[▶ Read the story →](https://pbchrist.github.io/voyd-terminal/)**

A living branching fantasy story. Faelspire has three bells. When a fourth one rings
beneath the city, something answers — and you are the cat standing closest to it.

You read a scene, you choose, the story continues. Nothing to install, nothing to
understand. Just read it.

---

## What makes it different

Most AI fiction is generated once and cached forever — a first draft nobody ever
edited. This isn't that.

Every scene here is **read cold by independent critics, judged on structure, character,
audience experience, interactivity and prose, diagnosed for its single weakest joint,
rewritten, and independently replayed** before it becomes canon. The writer is never
allowed to approve its own work.

The story gets *better over time*. And because every version is committed, you can see
exactly why each change happened.

## The living edge

Some paths end at a marker that says **The Living Edge**. That isn't a dead end — it's
the frontier. It means the Story Room hasn't written past that point yet.

Come back. It will have.

## For the curious

The fiction lives in [`story/scenes/`](story/scenes) as plain Markdown — that's the
product, and it outranks everything else in this repository. The current frontier is
tracked in [`story_room/frontier.json`](story_room/frontier.json).

The machinery that evolves it — agents, judges, the rubric, walkers, the autonomous
runner — lives under [`story_room/`](story_room) and [`scripts/`](scripts). The
[Storytelling Judgment Rubric](story_room/STORYTELLING_JUDGMENT_RUBRIC.md) is the
standard every scene is held to. It is deliberately diagnostic: there is no single
aggregate quality score, because a story is not the sum of forty numbers.

The reader itself is [`site/index.html`](site/index.html). It fetches the scenes at
runtime, so when the Story Room commits a new scene, the site simply has it.

---

*Older machinery from earlier generations of this project (`evolve.py`, `engine/`,
`frontend/`, `STORY.md`, `START_HERE.md`) is retained for provenance and is not the
current reader experience.*
