const socket = io();

const demoTranscript = [
  { speaker: "Sales Rep", text: "Thanks for taking the time today. What are you currently using for your sales process?" },
  { speaker: "Customer", text: "Right now we mostly use spreadsheets and our CRM, but it feels slow." },
  { speaker: "Sales Rep", text: "Got it. What part feels the most frustrating?" },
  { speaker: "Customer", text: "Mostly follow-ups and training new reps." },
  { speaker: "Customer", text: "I like the idea, but I am worried it might be too expensive." },
  { speaker: "Customer", text: "I would need to see if this actually saves us time." },
  { speaker: "Customer", text: "We are also looking at a competitor right now." },
  { speaker: "Sales Rep", text: "That makes sense. What would make one option clearly better for your team?" },
  { speaker: "Customer", text: "If it helped new reps ramp faster, we would be interested." },
  { speaker: "Customer", text: "Let us set up a meeting next week to look at the workflow with my manager." },
];

let callActive = false;
let transcriptIndex = 0;
let transcriptInterval = null;
let timerInterval = null;
let elapsedSeconds = 0;
let mediaStream = null;
const companyId = document.body.dataset.companyId;
const meetingId = document.body.dataset.meetingId;

const callStatus = document.getElementById("callStatus");
const timer = document.getElementById("timer");
const micStatus = document.getElementById("micStatus");
const aiMode = document.getElementById("aiMode");
const startCall = document.getElementById("startCall");
const stopCall = document.getElementById("stopCall");
const transcriptFeed = document.getElementById("transcriptFeed");
const manualTranscript = document.getElementById("manualTranscript");
const sendManualTranscript = document.getElementById("sendManualTranscript");
const lineCount = document.getElementById("lineCount");
const suggestedResponse = document.getElementById("suggestedResponse");
const suggestionState = document.getElementById("suggestionState");
const copyResponse = document.getElementById("copyResponse");
const refreshSuggestion = document.getElementById("refreshSuggestion");
const objection = document.getElementById("objection");
const sentiment = document.getElementById("sentiment");
const closeProbability = document.getElementById("closeProbability");
const callHealth = document.getElementById("callHealth");
const customerIntent = document.getElementById("customerIntent");
const buyingSignal = document.getElementById("buyingSignal");
const nextAction = document.getElementById("nextAction");
const urgencyLevel = document.getElementById("urgencyLevel");
const confidenceScore = document.getElementById("confidenceScore");
const summaryArea = document.getElementById("summaryArea");
const saveStatus = document.getElementById("saveStatus");
const keyMoments = document.getElementById("keyMoments");
const schedulingPanel = document.getElementById("schedulingPanel");
const scheduleStatus = document.getElementById("scheduleStatus");
const schedulePrompt = document.getElementById("schedulePrompt");
const meetingTitle = document.getElementById("meetingTitle");
const meetingTime = document.getElementById("meetingTime");
const meetingAgenda = document.getElementById("meetingAgenda");
const copySchedule = document.getElementById("copySchedule");

function setActiveState(isActive) {
  callActive = isActive;
  callStatus.textContent = isActive ? "Call Active" : "Call Inactive";
  callStatus.classList.toggle("active", isActive);
  callStatus.classList.toggle("inactive", !isActive);
  suggestionState.textContent = isActive ? "Listening" : "Waiting";
}

function formatTime(totalSeconds) {
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function startTimer() {
  elapsedSeconds = 0;
  timer.textContent = "00:00";
  clearInterval(timerInterval);
  timerInterval = setInterval(() => {
    elapsedSeconds += 1;
    timer.textContent = formatTime(elapsedSeconds);
  }, 1000);
}

function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
}

async function requestMicrophone() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    micStatus.textContent = "Mic unavailable";
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    micStatus.textContent = "Mic ready";

    // Future integration point: use MediaRecorder or AudioWorklet here to stream
    // real audio chunks to socket.emit("audio_chunk", chunk) for live STT.
    socket.emit("audio_chunk", { source: "browser_microphone", mock: true });
  } catch (error) {
    micStatus.textContent = "Mic blocked";
  }
}

function stopMicrophone() {
  if (!mediaStream) {
    return;
  }

  mediaStream.getTracks().forEach((track) => track.stop());
  mediaStream = null;
  micStatus.textContent = "Mic idle";
}

function appendTranscriptLine(line) {
  const item = document.createElement("div");
  item.className = `transcript-line ${line.speaker.toLowerCase().includes("customer") ? "customer" : "rep"}`;
  item.innerHTML = `<span class="speaker">${line.speaker}</span><span>${line.text}</span>`;
  transcriptFeed.appendChild(item);
  transcriptFeed.scrollTop = transcriptFeed.scrollHeight;
  lineCount.textContent = `${transcriptFeed.children.length} lines`;
}

function sendNextTranscriptLine() {
  if (!callActive) {
    return;
  }

  const line = demoTranscript[transcriptIndex % demoTranscript.length];
  transcriptIndex += 1;
  appendTranscriptLine(line);
  socket.emit("transcript_update", line);
}

function sendManualCustomerLine() {
  const text = manualTranscript?.value.trim();
  if (!text || !callActive) {
    return;
  }

  const line = { speaker: "Customer", text };
  appendTranscriptLine(line);
  socket.emit("transcript_update", line);
  manualTranscript.value = "";
  suggestionState.textContent = "Thinking";
}

function startMockTranscript() {
  clearInterval(transcriptInterval);
  sendNextTranscriptLine();
  transcriptInterval = setInterval(sendNextTranscriptLine, 3500);
}

function stopMockTranscript() {
  clearInterval(transcriptInterval);
  transcriptInterval = null;
}

function updateSuggestion(data) {
  suggestedResponse.textContent = data.suggested_response;
  objection.textContent = data.objection_detected;
  sentiment.textContent = data.sentiment;
  closeProbability.textContent = `${data.close_probability}%`;
  callHealth.textContent = data.call_health || "Stable";
  customerIntent.textContent = data.customer_intent;
  buyingSignal.textContent = data.buying_signal || "None";
  nextAction.textContent = data.next_action;
  urgencyLevel.textContent = data.urgency_level;
  confidenceScore.textContent = `Confidence ${Math.max(58, data.close_probability || 74)}%`;

  if (data.ai_mode === "real_ai") {
    suggestionState.textContent = "Real AI";
    if (aiMode) {
      aiMode.textContent = `Real AI: ${data.ai_model || "OpenAI"}`;
      aiMode.classList.add("real");
      aiMode.classList.remove("mock");
    }
  } else if (data.ai_mode === "mock_fallback") {
    suggestionState.textContent = "Mock fallback";
    if (aiMode) {
      aiMode.textContent = "Mock fallback";
      aiMode.classList.add("mock");
      aiMode.classList.remove("real");
    }
  } else {
    suggestionState.textContent = "Mock AI";
  }

  if (data.scheduling_intent) {
    schedulingPanel.classList.remove("inactive-panel");
    schedulingPanel.classList.add("active-panel");
    scheduleStatus.textContent = "Detected";
    schedulePrompt.textContent = "Buyer is open to a follow-up. Confirm the meeting focus before sending an invite.";
    meetingTitle.textContent = data.suggested_meeting_title || "Loading... follow-up demo";
    meetingTime.textContent = data.suggested_meeting_time || "Next week, 30 minutes";
    meetingAgenda.textContent = data.suggested_meeting_agenda || "Review pain points, demo live guidance, and confirm next steps.";
  }

  if (data.key_moment && data.key_moment !== "None") {
    const item = document.createElement("li");
    item.textContent = data.key_moment;
    keyMoments.prepend(item);
  }
}

function renderSummary(summary) {
  const moments = summary.key_moments.length ? summary.key_moments.join("; ") : "No key moments captured yet.";
  summaryArea.innerHTML = `
    <strong>${summary.headline}</strong><br>
    Transcript lines: ${summary.total_transcript_lines}<br>
    Objections: ${summary.detected_objections.join(", ")}<br>
    Final sentiment: ${summary.final_sentiment}<br>
    Close probability: ${summary.final_close_probability}%<br>
    Call health: ${summary.final_call_health}<br>
    Scheduling intent: ${summary.scheduling_intent ? "Detected" : "Not detected"}<br>
    Next action: ${summary.recommended_next_action}<br>
    Key moments: ${moments}
  `;
}

startCall.addEventListener("click", () => {
  transcriptFeed.innerHTML = "";
  keyMoments.innerHTML = "";
  summaryArea.textContent = "Live call in progress.";
  if (saveStatus) {
    saveStatus.textContent = "";
  }
  schedulingPanel.classList.add("inactive-panel");
  schedulingPanel.classList.remove("active-panel");
  scheduleStatus.textContent = "Idle";
  schedulePrompt.textContent = "Listening for meeting intent such as \"let's schedule\" or \"next week.\"";
  meetingTitle.textContent = "No meeting suggested yet";
  meetingTime.textContent = "Waiting for scheduling signal";
  meetingAgenda.textContent = "When intent appears, Loading... will draft the booking context.";
  transcriptIndex = 0;
  requestMicrophone();
  socket.emit("start_call", { company_id: companyId, meeting_id: meetingId });
});

stopCall.addEventListener("click", () => {
  socket.emit("stop_call");
});

copyResponse.addEventListener("click", async () => {
  await navigator.clipboard.writeText(suggestedResponse.textContent);
  copyResponse.textContent = "Copied";
  setTimeout(() => {
    copyResponse.textContent = "Copy Response";
  }, 1200);
});

refreshSuggestion.addEventListener("click", () => {
  socket.emit("request_ai_suggestion");
});

sendManualTranscript?.addEventListener("click", sendManualCustomerLine);
manualTranscript?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    sendManualCustomerLine();
  }
});

copySchedule.addEventListener("click", async () => {
  const text = `${meetingTitle.textContent}\n${meetingTime.textContent}\n${meetingAgenda.textContent}`;
  await navigator.clipboard.writeText(text);
  copySchedule.textContent = "Copied";
  setTimeout(() => {
    copySchedule.textContent = "Copy scheduling message";
  }, 1200);
});

socket.on("connect", () => {
  suggestionState.textContent = "Connected";
});

socket.on("call_started", () => {
  setActiveState(true);
  startTimer();
  startMockTranscript();
});

socket.on("call_stopped", (data) => {
  setActiveState(false);
  stopTimer();
  stopMockTranscript();
  stopMicrophone();
  renderSummary(data.summary);
  if (saveStatus) {
    if (data.note_saved) {
      saveStatus.innerHTML = `Call notes saved to this client. <a href="/notes/${data.note_id}">View saved notes</a>`;
    } else {
      saveStatus.textContent = "Demo call summary generated. Add a client to save notes automatically.";
    }
  }
});

socket.on("ai_suggestion", updateSuggestion);

socket.on("audio_received", () => {
  if (callActive) {
    micStatus.textContent = "Mic streaming";
  }
});
