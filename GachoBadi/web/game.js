// Phaser 3 front end for GachoBadi's live crew output (executable/main.py
// -> output/crew/*.json), not the old Dynamic Content Pipeline (that
// system -- run_content_pipeline.py, content_pipeline.py, rag.py,
// output/content_pipeline/ -- was removed; see git history if you need
// it). This client fetches output/crew/manifest.json plus every file it
// points to and reassembles them into one scene per resolved task
// ("tick"): the real resident personalities/appearances, the real
// building the Item Interaction Agent registered goose_actions for, and
// the real Goose Solution Planner verb plan become the goose's own
// five-verb controls (Honk/Grab/Drop/Duck/Dash), with the same "task
// counts once its plan is satisfied" mechanic gdd.txt describes. Use the
// Task panel's Prev/Next buttons to page through every task the crew
// generated, not just the first.
//
// Requires output/crew/ to already exist (`python3 executable/main.py`
// from GachoBadi/) and this page to be served from GachoBadi/'s root
// (`python3 -m http.server` run from GachoBadi/, not web/) -- serving
// from inside web/ makes the browser normalize "../output/..." outside
// the server root and 404. There is no embedded fallback snapshot
// anymore (the old one was frozen data from the removed pipeline, in a
// completely different JSON shape) -- if the fetch fails, this file
// reports why instead of silently playing stale data.

const WORLD_W = 960, WORLD_H = 640;
const TASK_RADIUS = 170; // how close the goose must be to the task's building to "count" a verb
const MEMENTO_HOME_DISTANCE = 130; // how far the memento can drift before its reset rule kicks in
const MEMENTO_RESET_DELAY_MS = 4000;

async function loadCrewData() {
  const base = "../output/crew/";
  let manifestRes;
  try {
    manifestRes = await fetch(base + "manifest.json", { cache: "no-store" });
  } catch (e) {
    throw new Error(
      `Could not reach ${base}manifest.json (${e.message}). Serve this page with ` +
      `"python3 -m http.server" run from GachoBadi/ (not web/), not by opening the file directly.`
    );
  }
  if (!manifestRes.ok) {
    throw new Error(
      `${base}manifest.json returned HTTP ${manifestRes.status}. Run "python3 executable/main.py" ` +
      `from GachoBadi/ first to generate output/crew/, then reload.`
    );
  }
  const manifest = await manifestRes.json();
  const records = await Promise.all(
    manifest.records.map((entry) =>
      fetch(base + entry.file, { cache: "no-store" })
        .then((r) => r.json())
        .then((payload) => ({ content_type: entry.content_type, payload }))
    )
  );
  return assembleCrewData(manifest, records);
}

// Every output/crew/*.json file is one agent's own record shape (see
// executable/main.py's OutputWriter calls) -- this regroups the flat,
// numbered file list back into the per-resident/per-building/per-task
// structure the scene actually needs, without inventing any field this
// file's own agents didn't already write.
function assembleCrewData(manifest, records) {
  const residents = {};
  const buildings = {};
  const items = {};
  const taskSets = [];
  const ticks = [];
  let completion = null;
  let verification = null;
  let layout = "";

  const resident = (name) => (residents[name] = residents[name] || {});
  const building = (name) => (buildings[name] = buildings[name] || {});

  records.forEach(({ content_type, payload }) => {
    switch (content_type) {
      case "personality":
        resident(payload.name).personality = payload;
        break;
      case "appearance":
        resident(payload.resident).appearance = payload.spec;
        break;
      case "relationship": {
        const [a, b] = payload.residents;
        const rel = { label: payload.label, backstory: payload.backstory };
        resident(a).relationships = resident(a).relationships || {};
        resident(b).relationships = resident(b).relationships || {};
        resident(a).relationships[b] = rel;
        resident(b).relationships[a] = rel;
        break;
      }
      case "island_layout":
        layout = payload.spec;
        break;
      case "building_design": {
        const b = building(payload.building);
        b.design = payload.spec;
        // BuildingDesignerAgent's spec always reads "<name> (<kind>): ..."
        // (see agents/runtime/building_designer_agent.py) -- kind isn't
        // its own field in this record, so pull it back out rather than
        // re-deriving it from the building's name.
        const kindMatch = (payload.spec || "").match(/\(([a-z]+)\):/i);
        b.kind = kindMatch ? kindMatch[1].toLowerCase() : "";
        break;
      }
      case "item_interaction_building": {
        const b = building(payload.building);
        b.goose_actions = payload.goose_actions;
        b.possible_outcomes = payload.possible_outcomes;
        b.affordance_spec = payload.spec;
        break;
      }
      case "item_interaction_item":
        items[payload.item] = payload;
        break;
      case "task_set":
        taskSets.push(payload);
        break;
      case "tick":
        ticks.push(payload);
        break;
      case "completion":
        completion = payload;
        break;
      case "verification":
        verification = payload;
        break;
      default:
        break; // unknown content_type -- ignore rather than crash
    }
  });

  ticks.sort((a, b) => a.task.task_id - b.task.task_id);

  return {
    game: manifest.game,
    catalogSize: manifest.catalog_size,
    sets: manifest.sets,
    layout,
    residents,
    buildings,
    items,
    taskSets,
    ticks,
    completion,
    verification,
  };
}

// VerbPlan.lines (agents/runtime/goose_solution_planner_agent.py) is
// already structured stage direction, one "Goose: <verb> ..." per legal
// action -- no need to regex-scan free-form prose like the old
// task_premise.final_output parser did. An unregistered verb (e.g. the
// documented "carries" fallback bug -- see workflow/README.md) simply
// won't match here and is silently dropped from the checklist, the same
// way workflow/'s own no_unregistered_verb check flags it server-side.
function parseVerbPlan(lines) {
  const verbs = [];
  (lines || []).forEach((line) => {
    const m = line.match(/Goose:\s*(Honk|Grab|Drop|Duck|Dash)\b/i);
    if (!m) return;
    const verb = m[1][0].toUpperCase() + m[1].slice(1).toLowerCase();
    if (!verbs.some((v) => v.toLowerCase() === verb.toLowerCase())) verbs.push(verb);
  });
  return verbs;
}

function buildingTextureKey(kind) {
  if (kind === "structure") return "building-structure";
  if (kind === "prop") return "building-prop";
  return "building-shop"; // default/"shop" -- also whatever an unrecognized kind falls back to
}

function roleSlug(role) {
  return (role || "default").toLowerCase().replace(/[^a-z0-9]+/g, "-");
}

function buildTextures(scene) {
  const g = scene.add.graphics();

  // Goose -- same silhouette as UntitledGooseGame_Multi_Agent's, since it's
  // the same character; only the verbs available to it differ per game.
  g.clear();
  g.fillStyle(0xffffff, 1);
  g.fillEllipse(24, 26, 34, 26);
  g.fillEllipse(30, 14, 16, 16);
  g.fillStyle(0x2b2b2b, 1);
  g.fillEllipse(35, 11, 4, 4);
  g.fillStyle(0xf4a300, 1);
  g.fillTriangle(38, 14, 48, 12, 38, 18);
  g.fillTriangle(14, 34, 8, 40, 18, 38);
  g.fillTriangle(24, 36, 20, 42, 28, 40);
  g.generateTexture("goose", 52, 46);

  // Resident sprites -- one color per role in the current roster
  // (build_island_seed in executable/main.py); any role this doesn't
  // recognize falls back to resident-default rather than erroring.
  const residentColors = { baker: 0xd35400, teacher: 0x4a69bd, "gym instructor": 0x27ae60 };
  Object.entries(residentColors).forEach(([role, color]) => {
    g.clear();
    g.fillStyle(0xead9c4, 1);
    g.fillCircle(18, 14, 12);
    g.fillStyle(color, 1);
    g.fillRoundedRect(4, 22, 28, 30, 6);
    g.generateTexture(`resident-${roleSlug(role)}`, 36, 52);
  });
  g.clear();
  g.fillStyle(0xead9c4, 1);
  g.fillCircle(18, 14, 12);
  g.fillStyle(0x95afc0, 1);
  g.fillRoundedRect(4, 22, 28, 30, 6);
  g.generateTexture("resident-default", 36, 52);

  // Shop (e.g. Hazel's Bakery): a simple house silhouette.
  g.clear();
  g.fillStyle(0xb08968, 1);
  g.fillRect(0, 40, 140, 80);
  g.fillStyle(0x8a4b2f, 1);
  g.fillTriangle(-6, 42, 70, 0, 146, 42);
  g.fillStyle(0xf7e7ce, 1);
  g.fillRect(58, 78, 24, 42);
  g.fillStyle(0xffe680, 0.85);
  g.fillRect(16, 56, 22, 22);
  g.fillRect(102, 56, 22, 22);
  g.generateTexture("building-shop", 140, 120);

  // Structure (e.g. Front Gate): two posts, a crossbar, a dark gap.
  g.clear();
  g.fillStyle(0x6b6b6b, 1);
  g.fillRect(10, 20, 18, 100);
  g.fillRect(112, 20, 18, 100);
  g.fillRect(0, 10, 140, 18);
  g.fillStyle(0x2b2b2b, 1);
  g.fillRect(55, 60, 30, 60);
  g.generateTexture("building-structure", 140, 120);

  // Prop (e.g. Garden Hose Stand): a post with a coiled hose.
  g.clear();
  g.fillStyle(0x5b7a4a, 1);
  g.fillRect(60, 30, 20, 90);
  g.fillStyle(0x2f8f3f, 1);
  g.fillCircle(70, 34, 26);
  g.fillStyle(0x184d20, 1);
  g.fillCircle(70, 34, 14);
  g.generateTexture("building-prop", 140, 120);

  // Memento: a small kept photo/keepsake -- warm frame, pale center.
  g.clear();
  g.fillStyle(0x7a5230, 1);
  g.fillRoundedRect(0, 0, 26, 26, 4);
  g.fillStyle(0xfff6dd, 1);
  g.fillRoundedRect(4, 4, 18, 18, 2);
  g.fillStyle(0xe8a13a, 1);
  g.fillCircle(13, 13, 5);
  g.generateTexture("memento", 26, 26);

  g.destroy();
}

class CrewScene extends Phaser.Scene {
  constructor(crewData) {
    super("CrewScene");
    this.crewData = crewData;
  }

  init(data) {
    const count = this.crewData.ticks.length;
    const requested = data && typeof data.tickIndex === "number" ? data.tickIndex : 0;
    this.tickIndex = count ? ((requested % count) + count) % count : 0;
  }

  preload() {}

  create() {
    buildTextures(this);
    this.physics.world.setBounds(0, 0, WORLD_W, WORLD_H);
    this.add.rectangle(WORLD_W / 2, WORLD_H / 2, WORLD_W, WORLD_H, 0x264d33);

    const data = this.crewData;
    const tick = data.ticks[this.tickIndex] || null;
    this.tick = tick;
    this.task = tick ? tick.task : null;

    const verbPlanLines = tick && tick.verb_plan ? tick.verb_plan.lines : [];
    this.requiredVerbList = parseVerbPlan(verbPlanLines);
    this.requiredVerbs = new Set(this.requiredVerbList.map((v) => v.toLowerCase()));
    this.doneVerbs = new Set();
    this.taskResolved = false;

    this.buildingName = (this.task && this.task.involves_building) || "";
    const buildingInfo = data.buildings[this.buildingName] || {};
    const targetName = (this.task && this.task.target_resident) || "";
    const otherName = (this.task && this.task.other_resident) || "";

    this.building = this.add.image(700, 260, buildingTextureKey(buildingInfo.kind));
    this.add.text(this.building.x, this.building.y + 78, this.buildingName || "(no building)", {
      fontFamily: "monospace", fontSize: "13px", color: "#ffe9c7",
    }).setOrigin(0.5);

    this.residents = {};
    const targetRole = targetName && data.residents[targetName] && data.residents[targetName].personality
      ? data.residents[targetName].personality.role
      : "";
    if (targetName) this.residents[targetName] = this.spawnResident(targetName, targetRole, 650, 340);
    if (otherName) {
      const otherRole = data.residents[otherName] && data.residents[otherName].personality
        ? data.residents[otherName].personality.role
        : "";
      this.residents[otherName] = this.spawnResident(otherName, otherRole, 220, 190);
    }

    const relationship = targetName && otherName && data.residents[targetName] && data.residents[targetName].relationships
      ? data.residents[targetName].relationships[otherName]
      : null;
    if (relationship) {
      this.add.text(WORLD_W / 2, 40, relationship.backstory, {
        fontFamily: "monospace", fontSize: "14px", color: "#dff7ff",
        backgroundColor: "#00000088", padding: { x: 10, y: 6 },
      }).setOrigin(0.5).setDepth(30);
    }

    const itemEntry = Object.values(data.items)[0] || null;
    const itemName = (itemEntry && itemEntry.item) || "a lost memento";
    this.memento = this.physics.add.sprite(220, 470, "memento");
    this.memento.setImmovable(true);
    this.memento.homeX = this.memento.x;
    this.memento.homeY = this.memento.y;
    this.memento.droppedAt = 0;
    this.mementoLabel = this.add.text(this.memento.x, this.memento.y - 20, itemName, {
      fontFamily: "monospace", fontSize: "11px", color: "#fff6cf",
    }).setOrigin(0.5);
    this.carrying = false;

    this.goose = this.physics.add.sprite(480, 500, "goose");
    this.goose.setCollideWorldBounds(true);
    this.goose.setDamping(true);
    this.goose.setDrag(0.0018);
    this.goose.setMaxVelocity(420, 420);
    this.goose.body.setCircle(18, 8, 10);
    this.goose.facing = -1;
    this.dashUntil = 0;
    this.dashDir = new Phaser.Math.Vector2(0, 0);
    this.duckUntil = 0;

    this.cursors = this.input.keyboard.createCursorKeys();
    this.keys = this.input.keyboard.addKeys({
      w: Phaser.Input.Keyboard.KeyCodes.W,
      a: Phaser.Input.Keyboard.KeyCodes.A,
      s: Phaser.Input.Keyboard.KeyCodes.S,
      d: Phaser.Input.Keyboard.KeyCodes.D,
      honk: Phaser.Input.Keyboard.KeyCodes.SPACE,
      grab: Phaser.Input.Keyboard.KeyCodes.E,
      drop: Phaser.Input.Keyboard.KeyCodes.R,
      duck: Phaser.Input.Keyboard.KeyCodes.Q,
      dash: Phaser.Input.Keyboard.KeyCodes.SHIFT,
    });

    this.buildTaskHud();
    this.buildLoreHud();

    // A task with zero legal-verb steps (e.g. every planned verb was
    // unregistered and got dropped by parseVerbPlan above) has nothing
    // left for the player to press -- count it resolved immediately
    // rather than leaving an unwinnable checklist on screen.
    if (this.task && this.requiredVerbs.size === 0) this.resolveTask();
  }

  spawnResident(name, role, x, y) {
    const key = this.textures.exists(`resident-${roleSlug(role)}`) ? `resident-${roleSlug(role)}` : "resident-default";
    const sprite = this.add.sprite(x, y, key);
    sprite.baseY = y;
    this.tweens.add({
      targets: sprite, y: y - 5, duration: 1000 + Math.random() * 400,
      yoyo: true, repeat: -1, ease: "Sine.easeInOut",
    });
    this.add.text(x, y - 34, name, {
      fontFamily: "monospace", fontSize: "12px", color: "#dff7ff",
    }).setOrigin(0.5);
    return sprite;
  }

  buildTaskHud() {
    const panel = window.hudTabs.task.panel;
    const total = this.crewData.ticks.length;
    const render = () => {
      panel.innerHTML = "";

      const nav = document.createElement("div");
      nav.style.marginBottom = "6px";
      const prev = document.createElement("button");
      prev.textContent = "< Prev";
      prev.onclick = () => this.scene.restart({ tickIndex: this.tickIndex - 1 });
      const next = document.createElement("button");
      next.textContent = "Next >";
      next.onclick = () => this.scene.restart({ tickIndex: this.tickIndex + 1 });
      const counter = document.createElement("span");
      counter.textContent = ` Task ${total ? this.tickIndex + 1 : 0} / ${total} `;
      nav.appendChild(prev);
      nav.appendChild(counter);
      nav.appendChild(next);
      panel.appendChild(nav);

      if (!this.task) {
        const none = document.createElement("div");
        none.textContent = "No tasks found in output/crew/ -- run executable/main.py first.";
        panel.appendChild(none);
        return;
      }

      const title = document.createElement("div");
      title.style.fontWeight = "bold";
      title.textContent = this.taskResolved ? "TASK RESOLVED" : "ACTIVE TASK";
      panel.appendChild(title);
      const premise = document.createElement("div");
      premise.textContent = this.task.description;
      premise.style.marginBottom = "6px";
      panel.appendChild(premise);
      this.requiredVerbList.forEach((verb) => {
        const line = document.createElement("div");
        const done = this.doneVerbs.has(verb.toLowerCase());
        line.textContent = `${done ? "☑" : "☐"} ${verb} near the ${this.buildingName || "building"}`;
        if (done) line.className = "task-verb-done";
        panel.appendChild(line);
      });
      if (this.taskResolved && this.reactionLine) {
        const reaction = document.createElement("div");
        reaction.style.marginTop = "6px";
        reaction.style.color = "#9be564";
        reaction.textContent = this.reactionLine;
        panel.appendChild(reaction);
      }
    };
    this._refreshTaskHud = render;
    render();
  }

  buildLoreHud() {
    const panel = window.hudTabs.lore.panel;
    panel.innerHTML = "";
    const addBlock = (title, text) => {
      if (!text) return;
      const t = document.createElement("div");
      t.style.fontWeight = "bold";
      t.style.marginTop = "6px";
      t.textContent = title;
      panel.appendChild(t);
      const body = document.createElement("div");
      body.textContent = text;
      panel.appendChild(body);
    };

    if (!this.tick) return;
    const data = this.crewData;
    const buildingInfo = data.buildings[this.buildingName] || {};
    addBlock("Building Designer Agent", buildingInfo.design);
    addBlock("Item Interaction Agent", buildingInfo.affordance_spec);
    if (this.tick.screenplay) addBlock("Writer / Director Agent", this.tick.screenplay.lines.join("\n"));
    if (this.tick.chain && this.tick.chain.steps.length) {
      addBlock("Chain Reaction Agent", this.tick.chain.steps.map((s) => `${s.actor}: ${s.action}`).join("\n"));
    }
    if (this.tick.news) addBlock("Newscaster Agent", this.tick.news.headline);

    const findings = (data.verification && data.verification.unresolved_findings || [])
      .filter((f) => f.task_id === this.task.task_id);
    if (findings.length) {
      addBlock(
        "⚠ workflow/ verification",
        findings.map((f) => `[${f.rule}] ${f.message}`).join("\n")
      );
    }
  }

  popText(x, y, msg, color) {
    const t = this.add.text(x, y, msg, {
      fontFamily: "monospace", fontSize: "16px", color: color || "#ffffff",
    }).setOrigin(0.5).setDepth(50);
    this.tweens.add({ targets: t, y: y - 40, alpha: 0, duration: 700, onComplete: () => t.destroy() });
  }

  // Every one of the goose's five verbs can satisfy a required plan step
  // as long as the goose is near the task's building -- the plan lines
  // ("Goose: Grab near the Hazel's Bakery.") never name a specific target
  // object either, so "verb pressed within range" is the faithful check,
  // matching gdd.txt's own goal-state-flag framing rather than inventing a
  // stricter one.
  registerVerb(verbLabel) {
    if (this.taskResolved || !this.task) return;
    const key = verbLabel.toLowerCase();
    if (!this.requiredVerbs.has(key) || this.doneVerbs.has(key)) return;
    const d = Phaser.Math.Distance.Between(this.goose.x, this.goose.y, this.building.x, this.building.y);
    if (d > TASK_RADIUS) {
      this.popText(this.goose.x, this.goose.y - 30, `too far from the building for "${verbLabel}"`, "#cccccc");
      return;
    }
    this.doneVerbs.add(key);
    this.popText(this.goose.x, this.goose.y - 30, `${verbLabel}!`, "#ffe66d");
    if (this._refreshTaskHud) this._refreshTaskHud();
    if (this.doneVerbs.size === this.requiredVerbs.size) this.resolveTask();
  }

  resolveTask() {
    this.taskResolved = true;
    this.popText(this.building.x, this.building.y - 90, "TASK RESOLVED", "#7cffb2");
    const otherName = this.task.other_resident;
    const otherSprite = otherName && this.residents[otherName];
    // The DirectorAgent's own staged cut of who does what (executable/
    // crew.py's _resolve_or_retire) -- the other resident's entry there
    // IS the reconciliation beat, more precisely sourced than re-parsing
    // it back out of prose.
    const reactionStep = this.tick.staged_actions.find((a) => a.actor === otherName);
    this.reactionLine = reactionStep ? `${reactionStep.actor}: ${reactionStep.action}` : (this.tick.news ? this.tick.news.headline : "");
    if (otherSprite) {
      this.tweens.add({ targets: otherSprite, scale: 1.2, duration: 150, yoyo: true });
      this.popText(otherSprite.x, otherSprite.y - 40, this.reactionLine || "reconciled!", "#9be564");
    }
    if (this._refreshTaskHud) this._refreshTaskHud();
  }

  doHonk() {
    this.popText(this.goose.x, this.goose.y - 30, "HONK!", "#fffb8f");
    this.cameras.main.shake(100, 0.002);
    this.registerVerb("Honk");
  }

  doGrab() {
    if (!this.carrying) {
      const d = Phaser.Math.Distance.Between(this.goose.x, this.goose.y, this.memento.x, this.memento.y);
      if (d < 60) {
        this.carrying = true;
        this.memento.droppedAt = 0;
        this.popText(this.goose.x, this.goose.y - 30, "grabbed the memento", "#9be564");
      }
    }
    this.registerVerb("Grab");
  }

  doDrop() {
    if (this.carrying) {
      this.carrying = false;
      this.memento.x = this.goose.x + this.goose.facing * 20;
      this.memento.y = this.goose.y + 10;
      this.memento.droppedAt = this.time.now;
      this.popText(this.goose.x, this.goose.y - 30, "set the memento down", "#9be564");
    }
    this.registerVerb("Drop");
  }

  doDuck() {
    this.duckUntil = this.time.now + 250;
    this.registerVerb("Duck");
  }

  doDash() {
    const dir = this.dashDir.lengthSq() > 0 ? this.dashDir.clone() : new Phaser.Math.Vector2(this.goose.facing, 0);
    dir.normalize();
    this.lastDashDir = dir;
    this.dashUntil = this.time.now + 160;
    this.registerVerb("Dash");
  }

  update(time) {
    const left = this.cursors.left.isDown || this.keys.a.isDown;
    const right = this.cursors.right.isDown || this.keys.d.isDown;
    const up = this.cursors.up.isDown || this.keys.w.isDown;
    const down = this.cursors.down.isDown || this.keys.s.isDown;

    if (time < this.dashUntil) {
      const dashSpeed = 560;
      this.goose.setVelocity(this.lastDashDir.x * dashSpeed, this.lastDashDir.y * dashSpeed);
    } else {
      const dir = new Phaser.Math.Vector2((right ? 1 : 0) - (left ? 1 : 0), (down ? 1 : 0) - (up ? 1 : 0));
      if (dir.lengthSq() > 0) {
        dir.normalize();
        this.dashDir.copy(dir);
        this.goose.facing = dir.x !== 0 ? Math.sign(dir.x) : this.goose.facing;
      }
      this.goose.setVelocity(dir.x * 190, dir.y * 190);
    }
    this.goose.setFlipX(this.goose.facing < 0);
    this.goose.setScale(1, time < this.duckUntil ? 0.7 : 1);

    if (this.carrying) {
      this.memento.x = this.goose.x + this.goose.facing * 20;
      this.memento.y = this.goose.y + 10;
    } else if (this.memento.droppedAt) {
      const away = Phaser.Math.Distance.Between(this.memento.x, this.memento.y, this.memento.homeX, this.memento.homeY);
      if (away > MEMENTO_HOME_DISTANCE && time - this.memento.droppedAt > MEMENTO_RESET_DELAY_MS) {
        this.tweens.add({
          targets: this.memento, x: this.memento.homeX, y: this.memento.homeY, duration: 500, ease: "Quad.easeInOut",
        });
        this.popText(this.memento.x, this.memento.y - 24, "drifts back -- nothing is ever lost", "#8fd3ff");
        this.memento.droppedAt = 0;
      }
    }
    this.mementoLabel.setPosition(this.memento.x, this.memento.y - 20);

    if (Phaser.Input.Keyboard.JustDown(this.keys.honk)) this.doHonk();
    if (Phaser.Input.Keyboard.JustDown(this.keys.grab)) this.doGrab();
    if (Phaser.Input.Keyboard.JustDown(this.keys.drop)) this.doDrop();
    if (Phaser.Input.Keyboard.JustDown(this.keys.duck)) this.doDuck();
    if (Phaser.Input.Keyboard.JustDown(this.keys.dash)) this.doDash();
  }
}

(async function boot() {
  let crewData;
  try {
    crewData = await loadCrewData();
  } catch (e) {
    document.getElementById("game-container").textContent = `Could not load crew output: ${e.message}`;
    return;
  }
  const config = {
    type: Phaser.AUTO,
    width: WORLD_W,
    height: WORLD_H,
    parent: "game-container",
    backgroundColor: "#12210f",
    physics: { default: "arcade", arcade: { debug: false } },
    scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: [new CrewScene(crewData)],
  };
  new Phaser.Game(config);
})();
