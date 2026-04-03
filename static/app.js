const form = document.getElementById("comparison-form");
const result = document.getElementById("result");
const statusText = document.getElementById("status");
const submitButton = document.getElementById("submit-button");

const samples = {
  equality: {
    vedic_principle:
      "Dharma as justice, fairness, and moral duty in social life.",
    constitutional_article:
      "Article 14: Equality before law and equal protection of the laws.",
  },
  harmony: {
    vedic_principle:
      "Atharva Vedic emphasis on social harmony, unity of thought, and collective well-being.",
    constitutional_article:
      "The Preamble and Article 51A(e): fraternity, dignity, and the duty to promote harmony.",
  },
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderError(message) {
  result.className = "result";
  result.innerHTML = `
    <div class="error-box">
      <h3 class="section-title">Request Failed</h3>
      <p class="section-copy">${escapeHtml(message)}</p>
    </div>
  `;
}

function renderAnalysis(data) {
  const themeMarkup = (data.themes || [])
    .map((theme) => `<span class="theme-chip">${escapeHtml(theme)}</span>`)
    .join("");

  result.className = "result analysis-card";
  result.innerHTML = `
    <div class="theme-row">${themeMarkup}</div>
    <section class="section-block">
      <h3 class="section-title">Similarity</h3>
      <p class="section-copy">${escapeHtml(data.similarity)}</p>
    </section>
    <section class="section-block">
      <h3 class="section-title">Explanation</h3>
      <p class="section-copy">${escapeHtml(data.explanation)}</p>
    </section>
    <section class="section-block">
      <h3 class="section-title">Application</h3>
      <p class="section-copy">${escapeHtml(data.application)}</p>
    </section>
  `;
}

function setLoadingState(isLoading) {
  submitButton.disabled = isLoading;
  submitButton.textContent = isLoading ? "Analyzing..." : "Analyze Similarity";
  statusText.textContent = isLoading
    ? "Generating a structured comparison..."
    : "Results will appear here in the required project format.";
}

document.querySelectorAll(".sample-button").forEach((button) => {
  button.addEventListener("click", () => {
    const sample = samples[button.dataset.sample];
    document.getElementById("vedic_principle").value = sample.vedic_principle;
    document.getElementById("constitutional_article").value =
      sample.constitutional_article;
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setLoadingState(true);

  const payload = {
    vedic_principle: document.getElementById("vedic_principle").value,
    constitutional_article: document.getElementById("constitutional_article").value,
    model: document.getElementById("model").value,
    reasoning_effort: document.getElementById("reasoning_effort").value,
  };

  try {
    const response = await fetch("/api/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || "Unexpected API error.");
    }

    renderAnalysis(data.result);
    statusText.textContent = "Comparison generated successfully.";
  } catch (error) {
    renderError(error.message);
    statusText.textContent = "The analysis could not be generated.";
  } finally {
    setLoadingState(false);
  }
});
