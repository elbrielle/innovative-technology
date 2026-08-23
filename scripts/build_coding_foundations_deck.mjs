#!/usr/bin/env node
/** Build the fully editable Coding Foundations Retrofit teacher deck. */

import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { Presentation, PresentationFile } = require("@oai/artifact-tool");

const ROOT = path.resolve(path.dirname(decodeURIComponent(new URL(import.meta.url).pathname)), "..");
const OUT_DIR = path.join(ROOT, "tmp/coding-foundations-retrofit/deck/output");
const SHOT_DIR = path.join(ROOT, "curriculum-assets/coding-foundations");
const FINAL_PPTX = path.join(OUT_DIR, "Smart_Solutions_Coding_Foundations_Retrofit_Teacher_Deck_2027.pptx");

const C = {
  navy: "#0B1426",
  navy2: "#13213B",
  white: "#FFFFFF",
  cream: "#FFFBE8",
  teal: "#00B8C8",
  green: "#54B68A",
  purple: "#A970FF",
  pink: "#FF6FAE",
  gold: "#FFD166",
  blue: "#56B4E9",
  ink: "#172033",
  muted: "#AFC1D6",
};

const TEKS_SOURCE = "https://tea.texas.gov/laws-and-rules/texas-administrative-code/19-tac-chapter-126";
const MAKECODE_DOCS = "https://arcade.makecode.com/docs";
const MAKECODE_JS = "https://arcade.makecode.com/javascript/statements";
const MAKECODE_LOOPS = "https://arcade.makecode.com/blocks/loops";
const MAKECODE_VARIABLES = "https://arcade.makecode.com/javascript/variables";

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

async function imageBytes(filePath) {
  const bytes = await fs.readFile(filePath);
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function addShape(slide, name, geometry, x, y, w, h, fill, lineFill = "none", lineWidth = 0, radius = undefined) {
  return slide.shapes.add({
    geometry,
    name,
    position: { left: x, top: y, width: w, height: h },
    fill,
    line: { style: "solid", fill: lineFill, width: lineWidth },
    ...(radius ? { borderRadius: radius } : {}),
  });
}

function addText(slide, name, text, x, y, w, h, size = 24, color = C.white, bold = false, align = "left", font = "Aptos") {
  const box = addShape(slide, name, "textbox", x, y, w, h, "none");
  box.text = text;
  box.text.style = { fontSize: size, color, bold, fontFamily: font, alignment: align };
  return box;
}

function addChrome(slide, kicker, day = "") {
  slide.background.fill = C.navy;
  addText(slide, "kicker", kicker.toUpperCase(), 48, 28, 480, 24, 13, C.teal, true);
  if (day) addText(slide, "day", day.toUpperCase(), 1120, 28, 112, 24, 13, C.muted, true, "right");
  addText(slide, "footer-left", "SMART SOLUTIONS · CODING FOUNDATIONS", 48, 686, 390, 16, 9, C.muted, false);
  addText(slide, "footer-right", "VILS 2027", 1120, 686, 112, 16, 9, C.muted, false, "right");
}

function addTitle(slide, title, subtitle = "", kicker = "Coding Foundations", day = "") {
  addChrome(slide, kicker, day);
  addText(slide, "title", title, 48, 64, 1168, 70, 34, C.white, true);
  if (subtitle) addText(slide, "subtitle", subtitle, 48, 132, 1130, 48, 18, C.muted, false);
}

function addCard(slide, name, x, y, w, h, heading, body, accent = C.teal, bodySize = 18) {
  const card = addShape(slide, name, "roundRect", x, y, w, h, C.cream, accent, 2, 14);
  addText(slide, `${name}-heading`, heading, x + 22, y + 18, w - 44, 36, 20, C.ink, true);
  addText(slide, `${name}-body`, body, x + 22, y + 64, w - 44, h - 82, bodySize, C.ink, false);
  return card;
}

function addCode(slide, name, code, x, y, w, h, size = 20) {
  addShape(slide, `${name}-frame`, "roundRect", x, y, w, h, "#07101E", C.teal, 2, 12);
  addText(slide, name, code, x + 22, y + 18, w - 44, h - 34, size, "#E8FFF8", false, "left", "Courier New");
}

function addFlow(slide, labels, y, colors = [C.teal, C.green, C.purple, C.pink, C.gold]) {
  const gap = 18;
  const width = (1168 - gap * (labels.length - 1)) / labels.length;
  labels.forEach((label, index) => {
    const x = 48 + index * (width + gap);
    addShape(slide, `flow-${index}`, "roundRect", x, y, width, 82, C.cream, colors[index % colors.length], 3, 16);
    addText(slide, `flow-label-${index}`, label, x + 12, y + 20, width - 24, 42, 17, C.ink, true, "center");
  });
}

function setNotes(slide, teacherNotes, sources = []) {
  const lines = [teacherNotes, "", "[Sources]", ...sources.map((source) => `- ${source}`)];
  slide.speakerNotes.textFrame.setText(lines.join("\n"));
  slide.speakerNotes.setVisible(true);
}

async function addScreenshot(slide, name, fileName, alt, x, y, w, h, fit = "contain") {
  slide.images.add({
    blob: await imageBytes(path.join(SHOT_DIR, fileName)),
    contentType: "image/png",
    alt,
    fit,
    geometry: "roundRect",
    borderRadius: 14,
    position: { left: x, top: y, width: w, height: h },
  });
  addShape(slide, `${name}-border`, "roundRect", x, y, w, h, "none", C.teal, 2, 14);
}

async function build() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });

  {
    const s = deck.slides.add();
    s.background.fill = C.navy;
    addText(s, "kicker", "SMART SOLUTIONS · CODING FOUNDATIONS", 72, 78, 540, 28, 16, C.teal, true);
    addText(s, "title", "Plan it. Test it. Code it.", 72, 170, 820, 90, 52, C.white, true);
    addText(s, "subtitle", "A reusable pseudocode routine plus a two-day bridge from blocks to text.", 72, 278, 760, 82, 26, C.muted);
    addFlow(s, ["PLAN", "NOTICE", "TEST", "REVISE", "TRANSFER"], 486);
    setNotes(s, "Use this deck only for the retrofit moments. Keep the existing Intro to CS, Video Game Design, and RVR decks for the rest of each unit.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "One Passport follows the whole coding arc", "Students add one checkpoint at a time instead of completing a second coding unit.");
    addFlow(s, ["1 · DECOMPOSE", "2 · PATTERNS", "3 · REVISE", "4 · TEXT CODE", "5 · RVR"], 250);
    addText(s, "takeaway", "The planning language stays stable while the programming surface changes.", 120, 420, 1040, 86, 30, C.white, true, "center");
    setNotes(s, "Show the five Passport pages. Tell students they complete only the checkpoint assigned today and keep the same document.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Pseudocode must be precise enough to execute", "A useful plan removes hidden assumptions without copying programming-language syntax.", "Pseudocode launch", "Day 1");
    addCard(s, "good", 88, 220, 500, 310, "USE", "Short commands\nIndent repeated steps\nName variables by purpose\nShow decisions and repetition\nEnd where the task is complete", C.green, 23);
    addCard(s, "avoid", 692, 220, 500, 310, "AVOID", "“Make it work”\nUnexplained jumps\nDirections only the writer understands\nCopying blocks without a plan\nDecorating before testing", C.pink, 23);
    setNotes(s, "Read one example aloud literally. Ask what a computer or partner would do when the direction is ambiguous.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Break one goal into smaller jobs", "Complete Passport Checkpoint 1 before opening Code.org.", "Pseudocode launch", "Day 1");
    addCard(s, "goal", 64, 220, 345, 250, "GOAL", "What must the finished program make happen?", C.teal, 24);
    addCard(s, "io", 468, 220, 345, 250, "INPUT + OUTPUT", "What enters the system?\nWhat should the system produce?", C.purple, 24);
    addCard(s, "subs", 872, 220, 345, 250, "SUBPROBLEMS", "What are the three or more smaller jobs?", C.gold, 24);
    addText(s, "prompt", "If a job is still vague, break it down again.", 160, 530, 960, 56, 28, C.white, true, "center");
    setNotes(s, "Model with the Angry Birds route or another route puzzle already in the lesson. Keep the decomposition brief; students still complete the existing coding task.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Write the route before touching the blocks", "Use commands another person can perform without asking what you meant.", "Pseudocode launch", "Day 1");
    addCode(s, "pseudo", "START\n  MOVE forward 2 spaces\n  TURN right\n  REPEAT 3 times\n    MOVE forward 1 space\n  END REPEAT\nEND", 120, 210, 520, 350, 27);
    addCard(s, "why", 720, 230, 420, 300, "CHECK THE PLAN", "Is every move observable?\nIs the repeated group indented?\nCould the numbers change?\nWhere would a variable help?", C.teal, 23);
    setNotes(s, "Students draft on Passport Checkpoint 1, then build the same route in Code.org. Pseudocode does not need to match a single vendor syntax.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Literal testing exposes the missing assumption", "The partner may follow only the written plan.", "Pseudocode launch", "Day 1");
    addFlow(s, ["READ", "EXECUTE", "STOP AT CONFUSION", "MARK THE LINE", "REVISE"], 230);
    addText(s, "stem", "“I stopped at ______ because the plan did not say ______.”", 110, 410, 1060, 70, 30, C.cream, true, "center");
    addText(s, "rule", "Do not explain the missing step until your partner marks it.", 190, 515, 900, 44, 22, C.muted, false, "center");
    setNotes(s, "Keep this to a fast partner test. The purpose is to create evidence for revision, not to grade reading performance.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Name the repeated pattern before using a loop", "Complete Passport Checkpoint 2 during Intro to CS Day 2.", "Patterns and variables", "Day 2");
    addCode(s, "pattern", "MOVE forward\nTURN right\nMOVE forward\nTURN right\nMOVE forward\nTURN right", 96, 218, 440, 300, 25);
    addCode(s, "loop", "REPEAT 3 times\n  MOVE forward\n  TURN right\nEND REPEAT", 730, 260, 390, 220, 27);
    addText(s, "arrow", "→", 590, 320, 90, 70, 54, C.gold, true, "center");
    setNotes(s, "Ask students to bracket the smallest useful repeated group before they name the loop.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Variables give changing details useful names", "Record a name, type, starting value, and operation in the Passport.", "Patterns and variables", "Day 2");
    addCard(s, "num", 70, 220, 350, 270, "NUMBER", "boxesRemaining = 12\nrows = 3\ncolumns = 4\n\nOperations: +  −  ×  ÷", C.teal, 22);
    addCard(s, "str", 465, 220, 350, 270, "STRING", "missionName =\n“Emergency Supply Grid”\n\nOperation: join text", C.purple, 22);
    addCard(s, "bool", 860, 220, 350, 270, "BOOLEAN", "priorityMode = true\ncarryingBox = false\n\nOperations: AND, OR, NOT", C.gold, 22);
    setNotes(s, "Students may first encounter variables in blocks. Require meaningful names and connect each type to what it can store or control.", [TEKS_SOURCE, MAKECODE_VARIABLES]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Abstraction turns one route into a reusable procedure", "Keep the repeated idea; replace the details that may change.", "Patterns and variables", "Day 2");
    addCode(s, "specific", "MOVE 4 spaces\nTURN right\nMOVE 4 spaces", 90, 220, 420, 210, 28);
    addCode(s, "general", "PROCEDURE moveAndTurn(distance, direction)\n  MOVE distance spaces\n  TURN direction\nEND PROCEDURE", 650, 210, 540, 250, 22);
    addText(s, "transfer", "Now the same plan can solve more than one route.", 180, 525, 920, 52, 28, C.cream, true, "center");
    setNotes(s, "Students do not need to write a programming-language function yet. The abstraction evidence is the generalized pseudocode and explanation.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Predict before pressing Run", "Complete the prediction column before the program produces evidence.", "Test and revise", "Day 3");
    addFlow(s, ["PREDICT", "RUN", "OBSERVE", "CHANGE ONE THING", "RUN AGAIN"], 230);
    addText(s, "question", "What do you expect the computer to do—and which instruction should cause it?", 110, 410, 1060, 86, 29, C.white, true, "center");
    setNotes(s, "This extends the existing Debugging Detective bug log. Students should not backfill a prediction after seeing the result.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "One controlled change makes the result explainable", "The evidence must connect a cause to an observed effect.", "Test and revise", "Day 3");
    addCard(s, "predict", 70, 220, 255, 240, "PREDICTION", "What should happen?", C.teal, 21);
    addCard(s, "observe", 365, 220, 255, 240, "OBSERVED", "What actually happened?", C.purple, 21);
    addCard(s, "change", 660, 220, 255, 240, "ONE CHANGE", "What exact line or value changed?", C.pink, 21);
    addCard(s, "result", 955, 220, 255, 240, "RESULT", "What changed after the test?", C.gold, 21);
    addText(s, "stem", "“When I changed ______, the program ______ because ______.”", 135, 520, 1010, 54, 26, C.cream, true, "center");
    setNotes(s, "Require three records in Passport Checkpoint 3. A screenshot alone does not replace the cause-and-effect record.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Revise the pseudocode—not only the blocks", "A better executable program should leave behind a better plan.", "Test and revise", "Day 3");
    addCard(s, "before", 100, 230, 440, 260, "BEFORE", "REPEAT 3 times\n  MOVE forward\nEND REPEAT", C.pink, 25);
    addCard(s, "after", 740, 230, 440, 260, "AFTER", "REPEAT 4 times\n  MOVE forward\n  CHECK for wall\nEND REPEAT", C.green, 25);
    addText(s, "claim", "Name the exact revision and the evidence that justified it.", 180, 535, 920, 44, 24, C.white, true, "center");
    setNotes(s, "Students copy one changed pseudocode line into the Passport and explain why the new algorithm is better.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Plan one game feature before adding it", "Complete Passport Checkpoint 4 at the start of Video Game Design Lesson 2.", "Game remix", "Lesson 2");
    addCard(s, "challenge", 70, 220, 350, 260, "FEATURE GOAL", "Challenge · reward · rule\nidentity choice · feedback\nprogression", C.purple, 22);
    addCard(s, "trigger", 465, 220, 350, 260, "TRIGGER", "WHEN ______ happens...", C.teal, 26);
    addCard(s, "response", 860, 220, 350, 260, "RESULT", "...the program SHOULD ______.", C.gold, 26);
    setNotes(s, "Students choose one of the two required remix features and plan it before editing the project. Keep the existing feature requirements and rubric.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "A when/should statement becomes pseudocode", "The feature plan predicts behavior before the code is changed.", "Game remix", "Lesson 2");
    addCode(s, "feature-code", "WHEN player overlaps reward\n  ADD 1 TO score\n  PLAY success sound\n  MOVE reward to new location\nEND WHEN", 175, 210, 930, 300, 28);
    addText(s, "test", "Test question: Does the reward change score, feedback, and position every time?", 140, 545, 1000, 44, 23, C.cream, true, "center");
    setNotes(s, "After students build the feature in blocks, they record the test result in the same Passport section.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    s.background.fill = C.navy;
    addText(s, "kicker", "TEXT-CODE BRIDGE", 72, 84, 360, 28, 16, C.teal, true);
    addText(s, "title", "Blocks show the structure.\nText makes every instruction visible.", 72, 190, 1040, 150, 48, C.white, true);
    addText(s, "subtitle", "Emergency Supply Grid · two class periods · MakeCode Arcade JavaScript", 72, 392, 1080, 48, 24, C.muted);
    addFlow(s, ["TRACE", "PREDICT", "RUN", "CHANGE", "EXPLAIN"], 525);
    setNotes(s, "This is the only new standalone bridge in the sprint. Students already have block-code experience from Video Game Design.", [TEKS_SOURCE, MAKECODE_DOCS]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Open a new project and select JavaScript", "No import or personal account is required for the core route.", "Text-code bridge", "Day 1");
    await addScreenshot(s, "makecode-open", "makecode-supply-grid-code.png", "MakeCode Arcade JavaScript editor showing the Emergency Supply Grid program", 70, 190, 760, 425, "contain");
    addCard(s, "steps", 875, 210, 330, 365, "START HERE", "1. Open arcade.makecode.com\n2. Choose New Project\n3. Name it Emergency Supply Grid\n4. Select JavaScript\n5. Keep the simulator visible", C.teal, 21);
    setNotes(s, "Model the route once. If the welcome tour covers the language tabs, close it before selecting JavaScript.", ["https://arcade.makecode.com/", MAKECODE_DOCS]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Read named variables from top to bottom", "Type, starting value, and purpose belong together.", "Text-code bridge", "Day 1");
    await addScreenshot(s, "makecode-vars", "makecode-supply-grid-variables.png", "MakeCode Arcade JavaScript editor showing named variables and nested loops", 60, 182, 780, 440, "contain");
    addCard(s, "trace-vars", 880, 205, 330, 350, "TRACE FOUR VALUES", "missionName → string\nrows / columns → numbers\npriorityMode → Boolean\nsuppliesPlaced → number\n\nPredict before running.", C.purple, 20);
    setNotes(s, "Use the Passport trace table. Students identify what each variable stores or controls before changing any value.", [MAKECODE_VARIABLES]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "The outer loop makes rows; the inner loop makes columns", "One complete inner loop places every supply in one row.", "Text-code bridge", "Day 1");
    addCode(s, "nested", "for (let row = 0; row < rows; row++) {\n  for (let column = 0; column < columns; column++) {\n    placeSupply(row, column)\n    suppliesPlaced += 1\n  }\n}", 120, 200, 1040, 300, 25);
    addText(s, "trace", "TRACE: row 0 → columns 0, 1, 2, 3 · then row 1 begins", 130, 540, 1020, 52, 25, C.cream, true, "center");
    setNotes(s, "Physically trace the first row with a finger. Ask how many times the inner loop runs and how many times the outer loop runs.", [MAKECODE_JS, MAKECODE_LOOPS]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "One calculation places every supply", "The formula uses both loop variables instead of twelve separate positions.", "Text-code bridge", "Day 1");
    addCode(s, "position", "x = 25 + column × 35\ny = 25 + row × 35", 155, 215, 470, 180, 34);
    addCard(s, "calc", 720, 205, 390, 240, "TRY row = 2, column = 3", "x = 25 + 3 × 35 = 130\ny = 25 + 2 × 35 = 95", C.gold, 24);
    addText(s, "meaning", "The same formula works for every cell in the grid.", 190, 520, 900, 48, 27, C.white, true, "center");
    setNotes(s, "Students calculate one position by hand, then point to the multiplication and addition operations in the code.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Run the grid and compare it with the prediction", "A 3 × 4 grid should produce 12 supply markers.", "Text-code bridge", "Day 1");
    await addScreenshot(s, "makecode-result", "makecode-supply-grid-result.png", "MakeCode Arcade simulator showing a three-row by four-column supply grid and score 12", 80, 180, 790, 445, "contain");
    addCard(s, "evidence", 910, 210, 300, 350, "EVIDENCE", "Grid screenshot\nVisible score\nPredicted total\nObserved total\nOne sentence explaining the nested loops", C.green, 21);
    setNotes(s, "If the grid does not match the prediction, students use the Passport test table before asking for a replacement project.", ["https://arcade.makecode.com/"]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Day 1: trace, predict, and repair", "Students read working text code before independently changing it.", "Text-code bridge", "Day 1");
    addCard(s, "trace-task", 70, 210, 340, 310, "TRACE", "Label the outer loop, inner loop, variables, data types, and operations.", C.teal, 22);
    addCard(s, "predict-task", 470, 210, 340, 310, "PREDICT", "Calculate suppliesPlaced and one x/y position before Run.", C.purple, 22);
    addCard(s, "repair-task", 870, 210, 340, 310, "REPAIR", "Correct one teacher-provided loop or value bug and record the evidence.", C.pink, 22);
    setNotes(s, "Supported route: give students the complete code and one highlighted bug. Core route: students identify the bug from the mismatched result.", [TEKS_SOURCE, MAKECODE_JS]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Day 2: change the grid with purpose", "The new version must still use text, named variables, operations, and nested loops.", "Text-code bridge", "Day 2");
    addCard(s, "core", 70, 195, 340, 360, "CORE", "Change rows and columns\nPredict the new total\nChange spacing without overlap\nRun and revise\nExplain both loops", C.teal, 21);
    addCard(s, "support", 470, 195, 340, 360, "SUPPORTED", "Use a partially completed code frame\nChoose from tested dimensions\nTrace with a row/column table\nExplain orally or in writing", C.green, 21);
    addCard(s, "extend", 870, 195, 340, 360, "EXTENSION", "Use priorityMode to change color or placement\nAdd a reusable function\nCreate one blocked cell\nExplain the new subproblem", C.gold, 21);
    setNotes(s, "Do not require the extension for proficiency. The core artifact already satisfies the text-code and nested-loop evidence when students can explain it.", [TEKS_SOURCE, MAKECODE_JS]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Evidence must show both code and thinking", "The final screenshot is necessary, but it is not the whole demonstration.", "Text-code bridge", "Day 2");
    addCard(s, "r1", 70, 200, 540, 165, "TEXT CODE", "Readable JavaScript with two nested loops and named variables.", C.teal, 20);
    addCard(s, "r2", 670, 200, 540, 165, "DATA + OPERATIONS", "String, number, Boolean, and visible operations on values.", C.purple, 20);
    addCard(s, "r3", 70, 405, 540, 165, "TEST EVIDENCE", "Prediction, screenshot, one controlled change, and observed result.", C.pink, 20);
    addCard(s, "r4", 670, 405, 540, 165, "EXPLANATION", "How the loops address row and column subproblems in the real context.", C.gold, 20);
    setNotes(s, "Score each category with the assignment rubric. Students may explain orally when documented by the teacher, but the code and test evidence remain required.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Reuse the same planning routine with RVR", "Complete Passport Checkpoint 5 before the drawing mission.", "RVR transfer", "Day 1");
    addFlow(s, ["ASSIGN ROLES", "SET MILESTONES", "WRITE PSEUDOCODE", "RUN LITERALLY", "REVISE"], 220);
    addCard(s, "roles", 110, 380, 470, 180, "ROLES", "Planner · programmer · tester/evidence lead", C.teal, 22);
    addCard(s, "timeline", 700, 380, 470, 180, "TIMELINE", "Plan approved · first run · revision run", C.gold, 22);
    setNotes(s, "Add this before students select Draw or Blocks. The planning evidence should name heading, speed, duration/distance, waits, and repeated actions.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "Let the robot expose the missing step", "The physical result makes vague pseudocode visible.", "RVR transfer", "Day 1");
    addCard(s, "plan", 70, 220, 330, 260, "PLAN", "What should the robot draw?", C.teal, 22);
    addCard(s, "run", 475, 220, 330, 260, "RUN", "What did it actually draw?", C.purple, 22);
    addCard(s, "revise", 880, 220, 330, 260, "REVISE", "Which exact command, value, or repeated group changed?", C.gold, 22);
    addText(s, "claim", "“The robot ______ because our pseudocode ______. We revised ______.”", 125, 535, 1030, 48, 25, C.cream, true, "center");
    setNotes(s, "Require the team to update the Passport after the first run. Do not accept a corrected robot program with an unchanged plan.", [TEKS_SOURCE]);
  }

  {
    const s = deck.slides.add();
    addTitle(s, "One planning language now connects three coding surfaces", "Students can explain how the same algorithm moved from blocks to text to a robot.", "Close and transfer", "Final");
    addCard(s, "blocks", 70, 220, 340, 270, "BLOCKS", "Sequence, event, loop, condition\n\nWhat structure did the blocks make visible?", C.teal, 21);
    addCard(s, "text", 470, 220, 340, 270, "TEXT", "Named types, operations, syntax, nested loops\n\nWhat became more explicit?", C.purple, 21);
    addCard(s, "robot", 870, 220, 340, 270, "ROBOT", "Heading, speed, distance, timing, physical evidence\n\nWhat did the real result reveal?", C.gold, 21);
    addText(s, "final-reflection", "Use one specific revision in the Passport final reflection.", 180, 540, 920, 46, 25, C.white, true, "center");
    setNotes(s, "Close with the final Passport reflection. This is the synthesis evidence for transfer across tools and contexts.", [TEKS_SOURCE]);
  }

  for (const [index, slide] of deck.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(2, "0")}`;
    await writeBlob(path.join(OUT_DIR, `${stem}.png`), await deck.export({ slide, format: "png", scale: 1 }));
    await fs.writeFile(path.join(OUT_DIR, `${stem}.layout.json`), await (await slide.export({ format: "layout" })).text());
  }
  await writeBlob(path.join(OUT_DIR, "deck-montage.webp"), await deck.export({ format: "webp", montage: true, scale: 1 }));
  const raw = await deck.inspect({ kind: "slide,textbox,shape,image,notes", maxChars: 200000 });
  await fs.writeFile(path.join(OUT_DIR, "raw-output.ndjson"), raw.ndjson);
  await fs.writeFile(path.join(OUT_DIR, "raw-output.json"), JSON.stringify(deck.toProto()));
  const pptx = await PresentationFile.exportPptx(deck);
  await pptx.save(FINAL_PPTX);
  console.log(JSON.stringify({ finalPptx: FINAL_PPTX, slideCount: deck.slides.items.length }));
}

build().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
