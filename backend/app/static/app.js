/* HTML and generated data come from Python. Only local UI enhancements live here. */
if (location.pathname === "/" && location.hash === "#text-generator") {
  location.replace("/text" + location.search);
}

function setExpanded(row, expanded) {
  row.hidden = !expanded;
  const personRow = row.previousElementSibling;
  personRow.classList.toggle("is-expanded", expanded);
  personRow.querySelectorAll("[data-toggle-details]").forEach(button => {
    button.setAttribute("aria-expanded", String(expanded));
    if (button.classList.contains("expand-button")) button.classList.toggle("rotated", expanded);
  });
}

document.querySelectorAll("[data-toggle-details]").forEach(button => {
  button.addEventListener("click", () => {
    const row = document.getElementById(button.getAttribute("aria-controls"));
    const expand = row.hidden;
    document.querySelectorAll(".detail-row").forEach(other => setExpanded(other, other === row && expand));
  });
});

const form = document.querySelector("[data-generator-form]");
if (form) {
  const original = new URLSearchParams(new FormData(form)).toString();
  const note = document.querySelector("[data-settings-note]");
  const originalNote = note.textContent;
  form.addEventListener("input", () => {
    const changed = new URLSearchParams(new FormData(form)).toString() !== original;
    note.classList.toggle("settings-changed", changed);
    note.textContent = changed ? "Settings changed. Generate to apply." : originalNote;
  });
}

document.querySelectorAll("[data-random-seed]").forEach(button => {
  button.hidden = false;
  button.addEventListener("click", () => {
    const input = document.getElementById("seed");
    // This chooses the request argument; all contact randomness stays in SQL.
    input.value = String(crypto.getRandomValues(new Uint32Array(1))[0]);
    input.dispatchEvent(new Event("input", { bubbles: true }));
  });
});

document.querySelectorAll("[data-copy-text]").forEach(button => {
  button.hidden = false;
  button.addEventListener("click", async () => {
    const text = document.getElementById("generated-text");
    const status = document.querySelector("[data-copy-status]");
    try {
      await navigator.clipboard.writeText(text.value);
      button.textContent = "Copied";
      status.textContent = "Text copied.";
      setTimeout(() => { button.textContent = "Copy text"; }, 3000);
    } catch {
      text.focus();
      text.select();
      status.textContent = "Clipboard access is unavailable. The text is selected for manual copying.";
    }
  });
});
