/* ==============================================================
   Find Your Coach — routing UI

   Renders and traverses `routes.json`. There is no classifier, no
   model call, and no hard-coded screen: every question, option, and
   result below comes from the route data, so changing the routing
   means editing JSON, not this file.

   Deliberately absent: local storage, URL state, analytics, and any
   network request other than fetching the route data itself.
   ============================================================== */

(function () {
  "use strict";

  var ROUTES_URL = "./routes.json";
  var SKILLS_BASE = "../skills";
  var COPY_FEEDBACK_MS = 3000;

  var stage = document.getElementById("stage");
  var progress = document.getElementById("progress");
  var progressLabel = document.getElementById("progress-label");
  var progressSteps = document.getElementById("progress-steps");
  var controls = document.getElementById("controls");
  var backButton = document.getElementById("back");
  var restartButton = document.getElementById("restart");

  /** Route data, indexed once loaded. */
  var routes = null;
  var questionsById = {};
  var resultsById = {};

  /** Ids of the questions answered so far, oldest first. */
  var trail = [];

  var copyTimer = null;

  /* ------------------------------------------------------------
     Small DOM helpers
     ------------------------------------------------------------ */

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined && text !== null) {
      node.textContent = text;
    }
    return node;
  }

  function clear(node) {
    while (node.firstChild) {
      node.removeChild(node.firstChild);
    }
  }

  function skillHref(skillName) {
    return SKILLS_BASE + "/" + skillName + "/SKILL.md";
  }

  /* ------------------------------------------------------------
     Route data
     ------------------------------------------------------------ */

  function indexRoutes(data) {
    questionsById = {};
    resultsById = {};

    (data.questions || []).forEach(function (question) {
      questionsById[question.id] = question;
    });
    (data.results || []).forEach(function (result) {
      resultsById[result.id] = result;
    });

    if (typeof data.skills_base === "string" && data.skills_base) {
      SKILLS_BASE = data.skills_base;
    }
  }

  /**
   * Number of questions on the longest path starting at `nodeId`.
   *
   * Recomputed per screen so the progress total is the worst case from
   * where the visitor actually is: the three main branches are three
   * questions deep, and the "I genuinely don't know" branch spends one
   * extra question working out which of them applies.
   *
   * `scripts/validate_finder.py` rejects cycles, so the guard here is
   * only so a hand-edited routes.json cannot hang the page.
   */
  function longestQuestionPath(nodeId, onPath) {
    var question = questionsById[nodeId];
    if (!question || onPath[nodeId]) {
      return 0;
    }
    onPath[nodeId] = true;
    var deepest = 0;
    (question.options || []).forEach(function (option) {
      var depth = longestQuestionPath(option.next, onPath);
      if (depth > deepest) {
        deepest = depth;
      }
    });
    delete onPath[nodeId];
    return deepest + 1;
  }

  /* ------------------------------------------------------------
     Progress
     ------------------------------------------------------------ */

  function renderProgress(questionId) {
    var finished = questionId === null;
    var currentStep = trail.length + (finished ? 0 : 1);
    var total = finished
      ? trail.length
      : trail.length + longestQuestionPath(questionId, {});

    progress.hidden = false;
    clear(progressSteps);

    for (var i = 1; i <= Math.max(total, 1); i += 1) {
      var step = el("li", "progress__step");
      if (finished || i < currentStep) {
        step.setAttribute("data-state", "done");
      } else if (i === currentStep) {
        step.setAttribute("data-state", "current");
      }
      progressSteps.appendChild(step);
    }

    progressLabel.textContent = finished
      ? "Recommendation ready"
      : "Question " + currentStep + " of at most " + total;
  }

  function renderControls(canGoBack, visible) {
    controls.hidden = !visible;
    backButton.disabled = !canGoBack;
  }

  /* ------------------------------------------------------------
     Rendering
     ------------------------------------------------------------ */

  /**
   * Move focus to the heading a render just produced, so keyboard and
   * screen-reader users land on the new content instead of the top of
   * the document. Skipped on the very first render, which would
   * otherwise steal focus on page load.
   */
  function focusHeading(heading, shouldFocus) {
    if (shouldFocus && heading) {
      heading.focus();
    }
  }

  function renderQuestion(question, shouldFocus) {
    clear(stage);

    var heading = el("h2", "question__text", question.text);
    heading.id = "question-" + question.id;
    heading.setAttribute("tabindex", "-1");
    stage.appendChild(heading);

    var list = el("div", "options");
    list.setAttribute("role", "group");
    list.setAttribute("aria-labelledby", heading.id);

    (question.options || []).forEach(function (option) {
      var button = el("button", "option", option.label);
      button.type = "button";
      button.setAttribute("data-option-id", option.id);
      button.addEventListener("click", function () {
        choose(question.id, option);
      });
      list.appendChild(button);
    });

    stage.appendChild(list);
    stage.setAttribute("aria-busy", "false");

    renderProgress(question.id);
    renderControls(trail.length > 0, true);
    focusHeading(heading, shouldFocus);
  }

  function renderSkillResult(result, shouldFocus) {
    var card = el("div", "result");

    card.appendChild(el("p", "result__eyebrow", "Recommendation"));

    var heading = el("h2", "result__title");
    heading.id = "result-" + result.id;
    heading.setAttribute("tabindex", "-1");
    heading.appendChild(document.createTextNode("Start with "));
    heading.appendChild(el("code", "result__skill", result.skill));
    card.appendChild(heading);

    card.appendChild(el("p", "result__reason", result.reason));

    card.appendChild(
      el("p", "result__section-label", "Starter prompt")
    );
    var prompt = el("p", "result__prompt", result.starter_prompt);
    prompt.id = "starter-prompt-" + result.id;
    card.appendChild(prompt);

    card.appendChild(buildCopyRow(result.starter_prompt, prompt.id));

    var meta = el("div", "result__meta");

    var read = el("p");
    read.appendChild(document.createTextNode("Read the skill: "));
    var link = el("a", null, "skills/" + result.skill + "/SKILL.md");
    link.href = skillHref(result.skill);
    read.appendChild(link);
    meta.appendChild(read);

    if (result.handoff && result.handoff.skill) {
      var handoff = el("p");
      handoff.appendChild(document.createTextNode("Common handoff: "));
      var handoffLink = el("a", null, result.handoff.skill);
      handoffLink.href = skillHref(result.handoff.skill);
      handoff.appendChild(handoffLink);
      if (result.handoff.note) {
        handoff.appendChild(
          document.createTextNode(" — " + result.handoff.note)
        );
      }
      meta.appendChild(handoff);
    }

    card.appendChild(meta);

    clear(stage);
    stage.appendChild(card);
    stage.setAttribute("aria-busy", "false");

    renderProgress(null);
    renderControls(trail.length > 0, true);
    focusHeading(heading, shouldFocus);
  }

  function renderNoMatchResult(result, shouldFocus) {
    var card = el("div", "result result--no-match");

    card.appendChild(el("p", "result__eyebrow", "No recommendation"));

    var heading = el(
      "h2",
      "result__title",
      result.headline || "No coaching mode fits this"
    );
    heading.id = "result-" + result.id;
    heading.setAttribute("tabindex", "-1");
    card.appendChild(heading);

    card.appendChild(el("p", "result__reason", result.reason));

    var meta = el("div", "result__meta");
    meta.appendChild(el("p", null, result.explanation));

    if (result.closest_skill && result.closest_skill.skill) {
      var closest = el("p");
      closest.appendChild(document.createTextNode("Closest coaching mode: "));
      var closestLink = el("a", null, result.closest_skill.skill);
      closestLink.href = skillHref(result.closest_skill.skill);
      closest.appendChild(closestLink);
      if (result.closest_skill.note) {
        closest.appendChild(
          document.createTextNode(" — " + result.closest_skill.note)
        );
      }
      meta.appendChild(closest);
    }

    card.appendChild(meta);

    clear(stage);
    stage.appendChild(card);
    stage.setAttribute("aria-busy", "false");

    renderProgress(null);
    renderControls(trail.length > 0, true);
    focusHeading(heading, shouldFocus);
  }

  /**
   * The copy control and its status line.
   *
   * The status text lives inside the `aria-live="polite"` stage, so
   * assistive technology announces the copied state without a second
   * nested live region competing with it.
   */
  function buildCopyRow(text, promptId) {
    var row = el("div", "result__actions");

    var copyButton = el("button", "button button--primary", "Copy starter prompt");
    copyButton.type = "button";
    copyButton.setAttribute("aria-describedby", promptId);

    var status = el("span", "copy-status", "");

    copyButton.addEventListener("click", function () {
      copyToClipboard(text).then(function (ok) {
        status.textContent = ok
          ? "Copied to clipboard."
          : "Copy failed — select the prompt above and copy it manually.";
        if (copyTimer) {
          window.clearTimeout(copyTimer);
        }
        copyTimer = window.setTimeout(function () {
          status.textContent = "";
        }, COPY_FEEDBACK_MS);
      });
    });

    row.appendChild(copyButton);
    row.appendChild(status);

    var restart = el("button", "button", "Start over");
    restart.type = "button";
    restart.addEventListener("click", function () {
      restartFinder();
    });
    row.appendChild(restart);

    return row;
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).then(
        function () {
          return true;
        },
        function () {
          return legacyCopy(text);
        }
      );
    }
    return Promise.resolve(legacyCopy(text));
  }

  /** Fallback for browsers or contexts without the async clipboard. */
  function legacyCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "readonly");
    area.style.position = "fixed";
    area.style.top = "-1000px";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var copied = false;
    try {
      copied = document.execCommand("copy");
    } catch (error) {
      copied = false;
    }
    document.body.removeChild(area);
    return copied;
  }

  function renderError(message) {
    clear(stage);

    var heading = el("h2", "error__title", "The questions could not load");
    heading.setAttribute("tabindex", "-1");
    stage.appendChild(heading);

    stage.appendChild(el("p", "error__body", message));

    var fallback = el("p", "error__body");
    fallback.appendChild(
      document.createTextNode("The same routing exists as plain text: ")
    );
    var link = el("a", null, "Which skill should I use?");
    link.href =
      "https://github.com/Far-200/think-before-code#which-skill-should-i-use";
    fallback.appendChild(link);
    fallback.appendChild(document.createTextNode(" in the README."));
    stage.appendChild(fallback);

    var retry = el("button", "button button--primary", "Try again");
    retry.type = "button";
    retry.addEventListener("click", function () {
      load();
    });
    stage.appendChild(retry);

    stage.setAttribute("aria-busy", "false");
    progress.hidden = true;
    renderControls(false, false);
  }

  /* ------------------------------------------------------------
     Traversal
     ------------------------------------------------------------ */

  function show(nodeId, shouldFocus) {
    if (questionsById[nodeId]) {
      renderQuestion(questionsById[nodeId], shouldFocus);
      return;
    }

    var result = resultsById[nodeId];
    if (!result) {
      renderError(
        "The route data points at '" +
          nodeId +
          "', which is neither a question nor a result."
      );
      return;
    }

    if (result.type === "skill") {
      renderSkillResult(result, shouldFocus);
    } else {
      renderNoMatchResult(result, shouldFocus);
    }
  }

  function choose(questionId, option) {
    trail.push({ question: questionId, option: option.id, next: option.next });
    show(option.next, true);
  }

  function goBack() {
    if (!trail.length) {
      return;
    }
    var last = trail.pop();
    show(last.question, true);
  }

  function restartFinder() {
    trail = [];
    show(routes.start, true);
  }

  /* ------------------------------------------------------------
     Boot
     ------------------------------------------------------------ */

  function load() {
    stage.setAttribute("aria-busy", "true");
    clear(stage);
    stage.appendChild(el("p", "stage__loading", "Loading the questions…"));

    fetch(ROUTES_URL, { cache: "no-cache" })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("routes.json responded with " + response.status);
        }
        return response.json();
      })
      .then(function (data) {
        routes = data;
        indexRoutes(data);
        if (!questionsById[data.start]) {
          throw new Error("routes.json has no starting question");
        }
        trail = [];
        show(data.start, false);
      })
      .catch(function (error) {
        renderError(
          "routes.json could not be read (" +
            error.message +
            "). If you opened this page directly from disk, serve the " +
            "repository over HTTP instead — browsers block file:// fetches."
        );
      });
  }

  backButton.addEventListener("click", goBack);
  restartButton.addEventListener("click", restartFinder);

  load();
})();
