"use strict";
const $ = (id) => document.getElementById(id);
let latestResult = null;
let busy = false;
const topic = $("topic");
function updateCount() { $("counter").textContent = `${topic.value.length} / 500`; }
topic.addEventListener("input", updateCount);
document.querySelectorAll("[data-topic]").forEach((button) => {
  button.addEventListener("click", () => {
    topic.value = button.dataset.topic;
    updateCount();
    topic.focus();
  });
});
function showStatus(message, error = false) {
  $("status").textContent = message;
  $("status").classList.toggle("error", error);
}
function renderAnswer(result, model) {
  latestResult = result;
  // AI의 답을 HTML로 실행하지 않고, 글자로만 표시합니다.
  for (const field of ["title", "summary", "explanation", "analogy"]) {
    $("answer-" + field).textContent = result[field];
  }
  $("answer-points").replaceChildren(...result.points.map((point) => {
    const item = document.createElement("li"); item.textContent = point; return item;
  }));
  $("quiz-question").textContent = result.quiz.question;
  $("quiz-answer").textContent = result.quiz.answer;
  $("answer").querySelector("details").open = false;
  $("result-meta").textContent = `Gemini · ${model} · 방금 만든 나의 학습 노트`;
  $("empty-state").hidden = true;
  $("answer").hidden = false;
  $("result-badge").textContent = "학습 노트 완성";
}
$("study-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy) return;
  const text = topic.value.trim();
  if (text.length < 2 || text.length > 500) {
    showStatus("궁금한 내용을 2~500자로 적어 주세요.", true); topic.focus(); return;
  }
  busy = true;
  $("submit-button").disabled = true;
  $("submit-button").textContent = "설명을 만들고 있어요…";
  $("empty-state").hidden = true;
  $("answer").hidden = true;
  $("loading-state").hidden = false;
  $("result-panel").setAttribute("aria-busy", "true");
  $("result-badge").textContent = "생각 중";
  showStatus("AI가 설명을 만들고 있어요. 잠시만 기다려 주세요.");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 48000);
  const slow = setTimeout(() => showStatus("답변이 조금 늦어지고 있어요. 조금만 더 기다려 주세요."), 12000);
  try {
    // 화면 → 나의 Python 백엔드 → Gemini → 화면 순서로 전달됩니다.
    const response = await fetch("/api/learn", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({topic: text, level: $("level").value}), signal: controller.signal
    });
    let data;
    try { data = await response.json(); }
    catch { throw new Error("서버의 응답을 읽지 못했어요. 잠시 뒤 다시 시도해 주세요."); }
    if (!response.ok) throw new Error(data.error || "AI 연결에 문제가 생겼어요. 잠시 뒤 다시 시도해 주세요.");
    const result = data.result;
    if (!result || !["title", "summary", "explanation", "analogy"].every(k => typeof result[k] === "string") ||
        !Array.isArray(result.points) || !result.points.every(p => typeof p === "string") ||
        typeof result.quiz?.question !== "string" || typeof result.quiz?.answer !== "string") {
      throw new Error("설명 형식이 올바르지 않아요. 다시 시도해 주세요.");
    }
    renderAnswer(result, data.model);
    showStatus("설명이 완성됐어요! 퀴즈도 풀어 보세요.");
    $("answer").focus({preventScroll:true});
    if (window.innerWidth <= 720) $("result-panel").scrollIntoView({behavior:"smooth", block:"start"});
  } catch (error) {
    showStatus(error.name === "AbortError" ? "답변이 너무 늦어 요청을 멈췄어요. 잠시 뒤 다시 눌러 주세요." :
      (error instanceof TypeError ? "인터넷 연결을 확인한 후 다시 시도해 주세요." : error.message), true);
    $("empty-state").hidden = Boolean(latestResult);
    $("answer").hidden = !latestResult;
    $("result-badge").textContent = latestResult ? "이전 학습 노트" : "다시 시도해 주세요";
  } finally {
    clearTimeout(timeout); clearTimeout(slow); busy = false;
    $("loading-state").hidden = true;
    $("result-panel").setAttribute("aria-busy", "false");
    $("submit-button").disabled = false;
    $("submit-button").textContent = "쉽게 풀어 주세요 ✦";
  }
});
$("download-button").addEventListener("click", () => {
  if (!latestResult) return;
  const r = latestResult;
  const text = `공부한입 학습 노트\n\n${r.title}\n\n[한 줄 요약]\n${r.summary}\n\n[쉬운 설명]\n${r.explanation}\n\n[일상 속 비유]\n${r.analogy}\n\n[기억할 것]\n${r.points.map(p => "- " + p).join("\n")}\n\n[확인 퀴즈]\n${r.quiz.question}\n\n[정답과 해설]\n${r.quiz.answer}\n\nAI 생성 내용입니다. 중요한 내용은 교재와 함께 확인하세요.\n`;
  const url = URL.createObjectURL(new Blob(["\ufeff", text], {type:"text/plain;charset=utf-8"}));
  const link = document.createElement("a"); link.href = url; link.download = "공부한입-학습노트.txt";
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
});
