// Phaser 3 front end for the UntitledGooseGame_Multi_Agent crew's output.
// The crew (main.py) generates output/run.json: villagers, props, and a
// mischief checklist. This file renders that data as a village and gives
// the player a maneuverable goose with the game's five verbs: Honk, Grab,
// Run, Tug, Flap. No dialogue is ever shown, matching the crew's own rule.

const ZONES = ["Garden", "High Street", "Back Gardens", "Pub", "Market", "Manor"];
const TILE_W = 480, TILE_H = 420, GUTTER = 40;
const WORLD_W = 3 * TILE_W + 4 * GUTTER;
const WORLD_H = 2 * TILE_H + 3 * GUTTER;

function zoneRect(index) {
  const r = Math.floor(index / 3), c = index % 3;
  const x = GUTTER + c * (TILE_W + GUTTER);
  const y = GUTTER + r * (TILE_H + GUTTER);
  return { x, y, w: TILE_W, h: TILE_H, cx: x + TILE_W / 2, cy: y + TILE_H / 2 };
}

async function loadVillageData() {
  // Prefer the live file (works when served over http://, e.g.
  // `python3 -m http.server` from this web/ folder) so re-running the crew
  // is instantly reflected. Fall back to the copy embedded in index.html
  // for a plain file:// double-click, where fetch() of a local file is
  // blocked by the browser.
  try {
    const res = await fetch("../output/run.json", { cache: "no-store" });
    if (res.ok) return await res.json();
  } catch (e) {
    // ignore -- fall through to embedded copy
  }
  const el = document.getElementById("village-data");
  return JSON.parse(el.textContent);
}

function buildTextures(scene) {
  const g = scene.add.graphics();

  // Goose: white oval body, black wingtip/eye accents, orange beak+feet.
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

  // A small feather puff, used for Flap particles.
  g.clear();
  g.fillStyle(0xffffff, 1);
  g.fillEllipse(6, 4, 12, 8);
  g.generateTexture("feather", 12, 8);

  const villagerColors = { gardener: 0x6ab04c, shopkeeper: 0x4a69bd, boy: 0xf6b93b };
  Object.entries(villagerColors).forEach(([role, color]) => {
    g.clear();
    g.fillStyle(0xead9c4, 1);
    g.fillCircle(18, 14, 12);
    g.fillStyle(color, 1);
    g.fillRoundedRect(4, 22, 28, 30, 6);
    g.generateTexture(`villager-${role}`, 36, 52);
  });
  g.clear();
  g.fillStyle(0xead9c4, 1);
  g.fillCircle(18, 14, 12);
  g.fillStyle(0x95afc0, 1);
  g.fillRoundedRect(4, 22, 28, 30, 6);
  g.generateTexture("villager-default", 36, 52);

  const propColors = {
    "garden tool": 0x8b5a2b,
    "clothing item": 0xd35400,
    toy: 0xe84393,
    "food item": 0xe1b12c,
    key: 0xbdc3c7,
  };
  Object.entries(propColors).forEach(([kind, color]) => {
    g.clear();
    g.fillStyle(color, 1);
    g.fillRoundedRect(2, 2, 24, 24, 5);
    g.lineStyle(2, 0x2c2c2c, 0.6);
    g.strokeRoundedRect(2, 2, 24, 24, 5);
    g.generateTexture(`prop-${kind}`, 28, 28);
  });
  g.clear();
  g.fillStyle(0xaaaaaa, 1);
  g.fillRoundedRect(2, 2, 24, 24, 5);
  g.generateTexture("prop-default", 28, 28);

  g.destroy();
}

class VillageScene extends Phaser.Scene {
  constructor(data) {
    super("VillageScene");
    this.villageData = data;
  }

  preload() {}

  create() {
    buildTextures(this);
    this.physics.world.setBounds(0, 0, WORLD_W, WORLD_H);

    this.add.rectangle(WORLD_W / 2, WORLD_H / 2, WORLD_W, WORLD_H, 0x2f6b3a);
    ZONES.forEach((name, i) => this.drawZone(name, i));

    const tick = this.villageData.mischief_tick || {};
    this.checklist = tick.checklist || [];
    this.propDefs = tick.props || [];
    this.villagerDefs = tick.villagers || [];

    this.propsByName = {};
    this.propSprites = this.physics.add.group();
    this.propDefs.forEach((p) => this.spawnProp(p));

    this.villagerSprites = this.physics.add.group({ immovable: true });
    this.villagersByName = {};
    this.villagerDefs.forEach((v) => this.spawnVillager(v));

    const startZone = zoneRect(0);
    this.goose = this.physics.add.sprite(startZone.cx, startZone.cy + 120, "goose");
    this.goose.setCollideWorldBounds(true);
    this.goose.setDamping(true);
    this.goose.setDrag(0.0018);
    this.goose.setMaxVelocity(420, 420);
    this.goose.body.setCircle(18, 8, 10);
    this.goose.facing = 1;

    this.carriedProp = null;
    this.dashUntil = 0;
    this.dashDir = new Phaser.Math.Vector2(0, 0);

    this.cameras.main.setBounds(0, 0, WORLD_W, WORLD_H);
    this.cameras.main.startFollow(this.goose, true, 0.12, 0.12);
    this.cameras.main.setZoom(1.1);

    this.cursors = this.input.keyboard.createCursorKeys();
    this.keys = this.input.keyboard.addKeys({
      w: Phaser.Input.Keyboard.KeyCodes.W,
      a: Phaser.Input.Keyboard.KeyCodes.A,
      s: Phaser.Input.Keyboard.KeyCodes.S,
      d: Phaser.Input.Keyboard.KeyCodes.D,
      honk: Phaser.Input.Keyboard.KeyCodes.SPACE,
      grab: Phaser.Input.Keyboard.KeyCodes.E,
      tug: Phaser.Input.Keyboard.KeyCodes.Q,
      flap: Phaser.Input.Keyboard.KeyCodes.F,
      run: Phaser.Input.Keyboard.KeyCodes.SHIFT,
    });

    this.buildHud();
  }

  drawZone(name, i) {
    const z = zoneRect(i);
    const shade = i % 2 === 0 ? 0x3c7d47 : 0x357240;
    const rect = this.add.rectangle(z.cx, z.cy, z.w, z.h, shade).setStrokeStyle(3, 0x1f4527);
    this.add.text(z.x + 12, z.y + 10, name, {
      fontFamily: "monospace",
      fontSize: "18px",
      color: "#e8f5e0",
    }).setDepth(1);
  }

  zoneCenterFor(locationName) {
    const idx = ZONES.indexOf(locationName);
    return zoneRect(idx >= 0 ? idx : 0);
  }

  spawnProp(propDef) {
    const z = this.zoneCenterFor(propDef.location);
    const jitterX = Phaser.Math.Between(-140, 140);
    const jitterY = Phaser.Math.Between(-100, 100);
    const key = `prop-${propDef.kind}`;
    const texKey = this.textures.exists(key) ? key : "prop-default";
    const sprite = this.physics.add.sprite(z.cx + jitterX, z.cy + jitterY, texKey);
    sprite.setImmovable(true);
    sprite.propName = propDef.name;
    sprite.carried = false;
    sprite.homeX = sprite.x;
    sprite.homeY = sprite.y;

    const label = this.add.text(sprite.x, sprite.y - 22, propDef.name, {
      fontFamily: "monospace",
      fontSize: "12px",
      color: "#fff6cf",
    }).setOrigin(0.5);
    sprite.label = label;

    this.propsByName[propDef.name] = sprite;
    this.propSprites.add(sprite);
  }

  spawnVillager(villagerDef) {
    const linkedItem = this.checklist.find((c) => c.target_villager === villagerDef.name);
    const prop = linkedItem ? this.propsByName[linkedItem.involves_prop] : null;
    const z = prop ? this.zoneCenterFor(this.propDefs.find((p) => p.name === prop.propName)?.location) : zoneRect(5);
    const jitterX = Phaser.Math.Between(-80, 80);
    const jitterY = Phaser.Math.Between(-60, 60);

    const key = `villager-${villagerDef.role}`;
    const texKey = this.textures.exists(key) ? key : "villager-default";
    const sprite = this.physics.add.sprite(z.cx + jitterX, z.cy + jitterY, texKey);
    sprite.setImmovable(true);
    sprite.villagerName = villagerDef.name;
    sprite.baseY = sprite.y;
    sprite.alerted = false;

    this.tweens.add({
      targets: sprite,
      y: sprite.baseY - 6,
      duration: 900 + Phaser.Math.Between(0, 400),
      yoyo: true,
      repeat: -1,
      ease: "Sine.easeInOut",
    });

    const label = this.add.text(sprite.x, sprite.y - 34, villagerDef.name, {
      fontFamily: "monospace",
      fontSize: "12px",
      color: "#dff7ff",
    }).setOrigin(0.5);
    sprite.label = label;

    this.villagersByName[villagerDef.name] = sprite;
    this.villagerSprites.add(sprite);
  }

  buildHud() {
    this.hudText = this.add.text(16, 16, "", {
      fontFamily: "monospace",
      fontSize: "14px",
      color: "#ffffff",
      backgroundColor: "#000000aa",
      padding: { x: 10, y: 8 },
    }).setScrollFactor(0).setDepth(100);

    this.helpText = this.add.text(16, 0, "", {
      fontFamily: "monospace",
      fontSize: "12px",
      color: "#d7ffd7",
      backgroundColor: "#000000aa",
      padding: { x: 10, y: 6 },
    }).setScrollFactor(0).setDepth(100);
    this.helpText.setText(
      "Move: WASD / Arrows   Run: hold Shift\n" +
      "Honk: Space   Grab: E   Tug: Q   Flap: F\n" +
      "Grab a prop, carry it to its villager, then Tug to complete the objective."
    );
    this.refreshChecklistHud();
    this.layoutHud();
    this.scale.on("resize", () => this.layoutHud());
  }

  layoutHud() {
    this.helpText.setPosition(16, this.scale.height - this.helpText.height - 16);
  }

  refreshChecklistHud() {
    const boxFor = (status) => {
      if (status === "done") return "✅";
      if (status === "retired") return "❌";
      return "⬜";
    };
    const lines = this.checklist.map((item) => {
      const suffix = item.status === "retired" ? " (unreachable, retired)" : "";
      return `${boxFor(item.status)} #${item.item_id} ${item.description}${suffix}`;
    });
    this.hudText.setText(["MISCHIEF CHECKLIST", ...lines].join("\n"));
  }

  popText(x, y, msg, color) {
    const t = this.add.text(x, y, msg, {
      fontFamily: "monospace",
      fontSize: "16px",
      color: color || "#ffffff",
    }).setOrigin(0.5).setDepth(50);
    this.tweens.add({
      targets: t,
      y: y - 40,
      alpha: 0,
      duration: 700,
      onComplete: () => t.destroy(),
    });
  }

  alertVillager(sprite) {
    if (sprite.alerted) return;
    sprite.alerted = true;
    this.popText(sprite.x, sprite.y - 40, "?!", "#ffe66d");
    this.tweens.add({
      targets: sprite,
      scale: 1.25,
      duration: 120,
      yoyo: true,
      onComplete: () => {
        sprite.alerted = false;
      },
    });
  }

  doHonk() {
    this.popText(this.goose.x, this.goose.y - 30, "HONK!", "#fffb8f");
    this.cameras.main.shake(120, 0.003);
    this.villagerSprites.children.iterate((sprite) => {
      if (!sprite) return;
      const d = Phaser.Math.Distance.Between(this.goose.x, this.goose.y, sprite.x, sprite.y);
      if (d < 170) this.alertVillager(sprite);
    });
  }

  doGrab() {
    if (this.carriedProp) {
      this.popText(this.goose.x, this.goose.y - 30, "already carrying", "#cccccc");
      return;
    }
    let nearest = null, nearestDist = 70;
    this.propSprites.children.iterate((sprite) => {
      if (!sprite || sprite.carried) return;
      const d = Phaser.Math.Distance.Between(this.goose.x, this.goose.y, sprite.x, sprite.y);
      if (d < nearestDist) {
        nearest = sprite;
        nearestDist = d;
      }
    });
    if (!nearest) return;
    nearest.carried = true;
    this.carriedProp = nearest;
    this.popText(this.goose.x, this.goose.y - 30, `grabbed ${nearest.propName}`, "#9be564");
  }

  doTug() {
    if (!this.carriedProp) {
      this.popText(this.goose.x, this.goose.y - 30, "nothing to tug", "#cccccc");
      return;
    }
    const prop = this.carriedProp;
    prop.carried = false;
    this.carriedProp = null;

    const flingX = prop.x + this.goose.facing * 46;
    this.tweens.add({ targets: [prop, prop.label], x: flingX, duration: 180, ease: "Quad.easeOut" });
    this.popText(prop.x, prop.y - 26, `dropped ${prop.propName}`, "#9be564");

    const item = this.checklist.find(
      (c) => c.involves_prop === prop.propName && c.status === "open"
    );
    if (!item) return;
    const villager = this.villagersByName[item.target_villager];
    if (villager) {
      const d = Phaser.Math.Distance.Between(prop.x, prop.y, villager.x, villager.y);
      if (d < 220) {
        item.status = "done";
        this.alertVillager(villager);
        this.popText(villager.x, villager.y - 50, "OBJECTIVE COMPLETE", "#7cffb2");
        this.refreshChecklistHud();
      }
    }
  }

  doFlap() {
    const dir = this.dashDir.lengthSq() > 0 ? this.dashDir.clone() : new Phaser.Math.Vector2(this.goose.facing, 0);
    dir.normalize();
    this.dashUntil = this.time.now + 180;
    this.lastDashDir = dir;

    for (let i = 0; i < 8; i++) {
      const f = this.add.image(
        this.goose.x - dir.x * 14 + Phaser.Math.Between(-6, 6),
        this.goose.y - dir.y * 14 + Phaser.Math.Between(-6, 6),
        "feather"
      ).setDepth(40);
      this.tweens.add({
        targets: f,
        x: f.x - dir.x * 40 + Phaser.Math.Between(-20, 20),
        y: f.y - dir.y * 40 + Phaser.Math.Between(-20, 20),
        alpha: 0,
        duration: 400,
        onComplete: () => f.destroy(),
      });
    }

    this.villagerSprites.children.iterate((sprite) => {
      if (!sprite) return;
      const d = Phaser.Math.Distance.Between(this.goose.x, this.goose.y, sprite.x, sprite.y);
      if (d < 90) this.alertVillager(sprite);
    });
  }

  update(time, delta) {
    const left = this.cursors.left.isDown || this.keys.a.isDown;
    const right = this.cursors.right.isDown || this.keys.d.isDown;
    const up = this.cursors.up.isDown || this.keys.w.isDown;
    const down = this.cursors.down.isDown || this.keys.s.isDown;

    if (time < this.dashUntil) {
      const dashSpeed = 620;
      this.goose.setVelocity(this.lastDashDir.x * dashSpeed, this.lastDashDir.y * dashSpeed);
    } else {
      const dir = new Phaser.Math.Vector2(
        (right ? 1 : 0) - (left ? 1 : 0),
        (down ? 1 : 0) - (up ? 1 : 0)
      );
      if (dir.lengthSq() > 0) {
        dir.normalize();
        this.dashDir.copy(dir);
        this.goose.facing = dir.x !== 0 ? Math.sign(dir.x) : this.goose.facing;
      }
      const running = this.keys.run.isDown;
      const speed = running ? 320 : 190;
      this.goose.setVelocity(dir.x * speed, dir.y * speed);
    }

    this.goose.setFlipX(this.goose.facing < 0);

    if (this.carriedProp) {
      this.carriedProp.x = this.goose.x + this.goose.facing * 22;
      this.carriedProp.y = this.goose.y + 6;
      this.carriedProp.label.setPosition(this.carriedProp.x, this.carriedProp.y - 22);
    }
    Object.values(this.propsByName).forEach((p) => {
      if (!this.carriedProp || p !== this.carriedProp) {
        p.label.setPosition(p.x, p.y - 22);
      }
    });
    Object.values(this.villagersByName).forEach((v) => {
      v.label.setPosition(v.x, v.y - 34);
    });

    if (Phaser.Input.Keyboard.JustDown(this.keys.honk)) this.doHonk();
    if (Phaser.Input.Keyboard.JustDown(this.keys.grab)) this.doGrab();
    if (Phaser.Input.Keyboard.JustDown(this.keys.tug)) this.doTug();
    if (Phaser.Input.Keyboard.JustDown(this.keys.flap)) this.doFlap();
  }
}

(async function boot() {
  const villageData = await loadVillageData();
  const config = {
    type: Phaser.AUTO,
    width: 960,
    height: 640,
    parent: "game-container",
    backgroundColor: "#12210f",
    physics: { default: "arcade", arcade: { debug: false } },
    scale: { mode: Phaser.Scale.RESIZE, autoCenter: Phaser.Scale.CENTER_BOTH },
    scene: [new VillageScene(villageData)],
  };
  new Phaser.Game(config);
})();
