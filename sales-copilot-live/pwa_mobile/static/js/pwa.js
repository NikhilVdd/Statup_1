let pwaDeferredPrompt = null;
let pwaTimerInterval = null;
let pwaSecondsRemaining = 60;

const pwaInstallButton = document.getElementById("pwa-install-button");
const pwaInstallSheet = document.getElementById("pwa-install-sheet");
const pwaInstallClose = document.getElementById("pwa-install-close");
const pwaTimer = document.getElementById("pwa-record-timer");
const pwaStatus = document.getElementById("pwa-record-status");
const pwaStartRecording = document.getElementById("pwa-start-recording");
const pwaStopRecording = document.getElementById("pwa-stop-recording");
const pwaSubmitPitch = document.getElementById("pwa-submit-pitch");

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/pwa/service-worker.js", { scope: "/pwa/" });
  });
}

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  pwaDeferredPrompt = event;
  if (pwaInstallButton) {
    pwaInstallButton.disabled = false;
    pwaInstallButton.textContent = "Install App";
  }
});

function pwaShowInstallSheet() {
  if (pwaInstallSheet) {
    pwaInstallSheet.classList.add("pwa-install-sheet-visible");
  }
}

function pwaHideInstallSheet() {
  if (pwaInstallSheet) {
    pwaInstallSheet.classList.remove("pwa-install-sheet-visible");
  }
}

pwaInstallButton?.addEventListener("click", async () => {
  if (!pwaDeferredPrompt) {
    pwaShowInstallSheet();
    return;
  }

  pwaDeferredPrompt.prompt();
  await pwaDeferredPrompt.userChoice;
  pwaDeferredPrompt = null;
});

pwaInstallClose?.addEventListener("click", pwaHideInstallSheet);

if (new URLSearchParams(window.location.search).get("install") === "1") {
  window.setTimeout(pwaShowInstallSheet, 450);
}

function pwaSetRecordStatus(message) {
  if (pwaStatus) {
    pwaStatus.textContent = message;
  }
}

function pwaRenderTimer() {
  if (pwaTimer) {
    pwaTimer.textContent = String(pwaSecondsRemaining).padStart(2, "0");
  }
}

function pwaStopTimer(message = "Recording stopped") {
  window.clearInterval(pwaTimerInterval);
  pwaTimerInterval = null;
  pwaSetRecordStatus(message);
}

function pwaStartTimer() {
  pwaSecondsRemaining = 60;
  pwaRenderTimer();
  pwaSetRecordStatus("Recording placeholder active");
  window.clearInterval(pwaTimerInterval);
  pwaTimerInterval = window.setInterval(() => {
    pwaSecondsRemaining -= 1;
    pwaRenderTimer();

    if (pwaSecondsRemaining <= 0) {
      pwaStopTimer("Time is up. Submit or try again.");
    }
  }, 1000);
}

pwaStartRecording?.addEventListener("click", pwaStartTimer);
pwaStopRecording?.addEventListener("click", () => pwaStopTimer("Recording placeholder stopped"));
pwaSubmitPitch?.addEventListener("click", () => {
  pwaStopTimer("Pitch submitted locally. Video upload coming later.");
});

pwaRenderTimer();
