// Phaser 3 front end for GachoBadi's Dynamic Content Pipeline
// (run_content_pipeline.py -> output/content_pipeline_run.json).
//
// Unlike UntitledGooseGame_Multi_Agent/web (which plays the *runtime crew's*
// output), this client plays the *content pipeline's* three RAG-grounded,
// critic-checked generations as an actual scene: the memento's affordance
// spec becomes a real pick-up-able prop, the Relationship Agent's authored
// backstory becomes Hazel/Otto's intro caption, and the task premise's
// (critic-corrected) goose-verb plan becomes the goose's own five-verb
// controls (Honk/Grab/Pick up/Duck/Dash) with the same "task counts once
// its plan is satisfied" mechanic the GDD describes -- see gdd.txt's
// "How a task is confirmed complete."
//
// The Consistency Critic panel shows every record's pass/fail and, for the
// task premise, the exact lore break it caught (an Untitled-Goose-Game
// verb, "Run," left over from agents/dynamic_content/task_premise_content_agent.py's
// CONNECTION_KINDS table)
// and the corrected text -- the same audit trail as
// output/content_pipeline_run.json, just visible in the running game.

const WORLD_W = 960, WORLD_H = 640;
const TASK_RADIUS = 170; // how close the goose must be to the task's building to "count" a verb
const MEMENTO_HOME_DISTANCE = 130; // how far the memento can drift before its reset rule kicks in
const MEMENTO_RESET_DELAY_MS = 4000;

async function loadPipelineData() {
  // Prefer the live file. IMPORTANT: this only resolves correctly if the
  // http server's root is GachoBadi/ itself (`python3 -m http.server` run
  // from GachoBadi, then open /web/index.html) -- serving from inside
  // web/ makes the browser normalize "../output/..." to a path outside
  // the server root and 404 (verified: a server rooted at web/ 404s this
  // fetch and silently falls back to the embedded copy below every time,
  // which still "works" but never reflects a fresh pipeline run). Falls
  // back to the copy embedded in index.html either way, e.g. for a plain
  // file:// double-click, where fetch() of a local file is blocked outright.
  try {
    const res = await fetch("../output/content_pipeline_run.json", { cache: "no-store" });
    if (res.ok) return await res.json();
  } catch (e) {
    // ignore -- fall through to embedded copy
  }
  const el = document.getElementById("pipeline-data");
  return JSON.parse(el.textContent);
}

function recordsByType(data) {
  const byType = {};
  (data.records || []).forEach((r) => { byType[r.content_type] = r; });
  return byType;
}

// The task premise's final_output (already critic-corrected) looks like:
//   Help Hazel and Otto patch up a disagreement at the Hazel's Bakery.
//   Goose: Grab near the Hazel's Bakery.
//   Goose: Dash near the Hazel's Bakery.
//   Goose: Honk near the Hazel's Bakery.
//   Otto: startles, then laughs off the disagreement with Hazel
// This pulls the premise line, the ordered (deduped) required verbs, and
// the reaction line back out -- the plan's own structure, not re-invented.
function parseTaskPlan(taskRecord) {
  const lines = (taskRecord.final_output || "").split("\n").map((l) => l.trim()).filter(Boolean);
  const premise = lines[0] || "";
  const verbs = [];
  let reactionLine = "";
  lines.slice(1).forEach((line) => {
    const verbMatch = line.match(/^Goose:\s*(Honk|Grab|Pick up|Duck|Dash)\b/i);
    if (verbMatch) {
      const verb = verbMatch[1];
      if (!verbs.some((v) => v.toLowerCase() === verb.toLowerCase())) verbs.push(verb);
      return;
    }
    if (/^\w[\w'’]*:\s/.test(line)) reactionLine = line;
  });
  return { premise, verbs, reactionLine };
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

  const residentColors = { baker: 0xd35400, teacher: 0x4a69bd };
  Object.entries(residentColors).forEach(([role, color]) => {
    g.clear();
    g.fillStyle(0xead9c4, 1);
    g.fillCircle(18, 14, 12);
    g.fillStyle(color, 1);
    g.fillRoundedRect(4, 22, 28, 30, 6);
    g.generateTexture(`resident-${role}`, 36, 52);
  });
  g.clear();
  g.fillStyle(0xead9c4, 1);
  g.fillCircle(18, 14, 12);
  g.fillStyle(0x95afc0, 1);
  g.fillRoundedRect(4, 22, 28, 30, 6);
  g.generateTexture("resident-default", 36, 52);

  // Bakery building: a simple house silhouette (walls + roof + window).
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
  g.generateTexture("bakery", 140, 120);

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

class PipelineScene extends Phaser.Scene {
  constructor(data) {
    super("PipelineScene");
    this.pipelineData = data;
  }

  preload() {}

  create() {
    buildTextures(this);
    this.physics.world.setBounds(0, 0, WORLD_W, WORLD_H);
    this.add.rectangle(WORLD_W / 2, WORLD_H / 2, WORLD_W, WORLD_H, 0x264d33);

    const records = recordsByType(this.pipelineData);
    this.itemRecord = records.item_affordance || null;
    this.backstoryRecord = records.relationship_backstory || null;
    this.taskRecord = records.task_premise || null;
    this.plan = this.taskRecord
      ? parseTaskPlan(this.taskRecord)
      : { premise: "", verbs: [], reactionLine: "" };
    this.requiredVerbs = new Set(this.plan.verbs.map((v) => v.toLowerCase()));
    this.doneVerbs = new Set();
    this.taskResolved = false;

    const buildingName = (this.taskRecord && this.taskRecord.meta && this.taskRecord.meta.building) || "Hazel's Bakery";
    const residentName = (this.taskRecord && this.taskRecord.meta && this.taskRecord.meta.resident) || "Hazel";
    const otherName = (this.taskRecord && this.taskRecord.meta && this.taskRecord.meta.other) || "Otto";

    this.building = this.add.image(700, 260, "bakery");
    this.add.text(this.building.x, this.building.y + 78, buildingName, {
      fontFamily: "monospace", fontSize: "13px", color: "#ffe9c7",
    }).setOrigin(0.5);

    this.residents = {};
    this.residents[residentName] = this.spawnResident(residentName, "baker", 650, 340);
    this.residents[otherName] = this.spawnResident(otherName, "teacher", 220, 190);

    if (this.backstoryRecord) {
      this.add.text(WORLD_W / 2, 40, this.backstoryRecord.final_output, {
        fontFamily: "monospace", fontSize: "14px", color: "#dff7ff",
        backgroundColor: "#00000088", padding: { x: 10, y: 6 },
      }).setOrigin(0.5).setDepth(30);
    }

    const itemName = (this.itemRecord && this.itemRecord.meta && this.itemRecord.meta.item_name) || "a lost memento";
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
      pickup: Phaser.Input.Keyboard.KeyCodes.R,
      duck: Phaser.Input.Keyboard.KeyCodes.Q,
      dash: Phaser.Input.Keyboard.KeyCodes.SHIFT,
    });

    this.buildTaskHud();
    this.buildLoreHud();
    this.buildCriticHud();
  }

  spawnResident(name, role, x, y) {
    const key = this.textures.exists(`resident-${role}`) ? `resident-${role}` : "resident-default";
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
    const render = () => {
      panel.innerHTML = "";
      const title = document.createElement("div");
      title.style.fontWeight = "bold";
      title.textContent = this.taskResolved ? "TASK RESOLVED" : "ACTIVE TASK";
      panel.appendChild(title);
      const premise = document.createElement("div");
      premise.textContent = this.plan.premise;
      premise.style.marginBottom = "6px";
      panel.appendChild(premise);
      this.plan.verbs.forEach((verb) => {
        const line = document.createElement("div");
        const done = this.doneVerbs.has(verb.toLowerCase());
        line.textContent = `${done ? "☑" : "☐"} ${verb} near the ${(this.taskRecord.meta || {}).building || "building"}`;
        if (done) line.className = "task-verb-done";
        panel.appendChild(line);
      });
      if (this.taskResolved && this.plan.reactionLine) {
        const reaction = document.createElement("div");
        reaction.style.marginTop = "6px";
        reaction.style.color = "#9be564";
        reaction.textContent = this.plan.reactionLine;
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
      const t = document.createElement("div");
      t.style.fontWeight = "bold";
      t.style.marginTop = "6px";
      t.textContent = title;
      panel.appendChild(t);
      const body = document.createElement("div");
      body.textContent = text;
      panel.appendChild(body);
    };
    if (this.itemRecord) addBlock("Item Interaction Content Agent", this.itemRecord.final_output);
    if (this.backstoryRecord) addBlock("Relationship Backstory Content Agent", this.backstoryRecord.final_output);
    if (this.taskRecord) addBlock("Task Premise Content Agent", this.taskRecord.final_output);
  }

  buildCriticHud() {
    const panel = window.hudTabs.critic.panel;
    panel.innerHTML = "";
    const title = document.createElement("div");
    title.style.fontWeight = "bold";
    title.textContent = "CONSISTENCY CRITIC AGENT";
    panel.appendChild(title);
    (this.pipelineData.records || []).forEach((r) => {
      const row = document.createElement("div");
      row.style.marginTop = "6px";
      const status = document.createElement("div");
      status.className = r.passed_critic ? "critic-pass" : "critic-fail";
      status.textContent = `${r.content_type}: ${r.passed_critic ? "passed" : `corrected (${r.critic_violations.length} issue(s))`}`;
      row.appendChild(status);
      r.critic_violations.forEach((v) => {
        const vline = document.createElement("div");
        vline.style.fontSize = "12px";
        vline.textContent = `- ${v}`;
        row.appendChild(vline);
      });
      panel.appendChild(row);
    });
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
    if (this.taskResolved || !this.taskRecord) return;
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
    const otherName = (this.taskRecord.meta || {}).other;
    const otherSprite = otherName && this.residents[otherName];
    if (otherSprite) {
      this.tweens.add({ targets: otherSprite, scale: 1.2, duration: 150, yoyo: true });
      this.popText(otherSprite.x, otherSprite.y - 40, this.plan.reactionLine || "reconciled!", "#9be564");
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

  doPickUp() {
    if (this.carrying) {
      this.carrying = false;
      this.memento.x = this.goose.x + this.goose.facing * 20;
      this.memento.y = this.goose.y + 10;
      this.memento.droppedAt = this.time.now;
      this.popText(this.goose.x, this.goose.y - 30, "set the memento down", "#9be564");
    }
    this.registerVerb("Pick up");
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
    if (Phaser.Input.Keyboard.JustDown(this.keys.pickup)) this.doPickUp();
    if (Phaser.Input.Keyboard.JustDown(this.keys.duck)) this.doDuck();
    if (Phaser.Input.Keyboard.JustDown(this.keys.dash)) this.doDash();
  }
}

(async function boot() {
  const pipelineData = await loadPipelineData();
  const config = {
    type: Phaser.AUTO,
    width: WORLD_W,
    height: WORLD_H,
    parent: "game-container",
    backgroundColor: "#12210f",
    physics: { default: "arcade", arcade: { debug: false } },
    scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: [new PipelineScene(pipelineData)],
  };
  new Phaser.Game(config);
})();
