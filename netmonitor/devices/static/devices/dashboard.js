(() => {
  "use strict";

  const body = document.body;
  const notificationButton = document.querySelector(".hero-action.notifications");
  const notificationStorageKey = "netwatch.notificationCount";
  const scanStatus = document.getElementById("scan-status");
  let activeModalTrigger = null;
  let pendingNotification = false;
  let autoScanInFlight = false;

  function readStoredNotificationCount() {
    try {
      return Number(window.localStorage.getItem(notificationStorageKey) || 0);
    } catch {
      return 0;
    }
  }

  function storeNotificationCount(count) {
    try {
      window.localStorage.setItem(notificationStorageKey, String(count));
    } catch {
      // Storage can be unavailable in private or restricted browser modes.
    }
  }

  function getNotificationCount() {
    const countElement = notificationButton?.querySelector("strong");
    const count = Number(countElement?.textContent?.trim() || 0);
    return Number.isFinite(count) && count > 0 ? count : 0;
  }

  function speakNotification(message) {
    if (!("speechSynthesis" in window)) {
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(message);
      utterance.lang = "en-US";
      utterance.rate = 1.02;
      utterance.pitch = 1.05;
      utterance.volume = 0.9;
      window.speechSynthesis.speak(utterance);
    } catch (error) {
      console.warn("Voice notification unavailable", error);
    }
  }

  async function playNotificationSound() {
    const count = getNotificationCount();

    if (count <= 0) {
      storeNotificationCount(0);
      return;
    }

    try {
      const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;

      if (AudioContextConstructor) {
        const audioContext = new AudioContextConstructor();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.type = "sine";
        oscillator.frequency.value = 880;
        gainNode.gain.setValueAtTime(0.04, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.0001, audioContext.currentTime + 0.2);

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.2);
        oscillator.addEventListener("ended", () => audioContext.close(), { once: true });
      }
    } catch (error) {
      console.warn("Notification sound unavailable", error);
    }

    const message = count === 1 ? "You have one notification." : `You have ${count} notifications.`;
    speakNotification(message);
    storeNotificationCount(count);
    pendingNotification = false;
  }

  function prepareNotificationAlert() {
    const currentCount = getNotificationCount();
    const previousCount = readStoredNotificationCount();

    if (currentCount <= 0) {
      storeNotificationCount(0);
      return;
    }

    pendingNotification = currentCount > previousCount;
    storeNotificationCount(currentCount);
  }

  function findFocusableElements(container) {
    return Array.from(
      container.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), ' +
          'select:not([disabled]), textarea:not([disabled]), ' +
          '[tabindex]:not([tabindex="-1"])'
      )
    ).filter((element) => !element.hasAttribute("hidden"));
  }

  function openModal(trigger) {
    const targetId = trigger.dataset.modalTarget;
    const modal = targetId ? document.getElementById(targetId) : null;

    if (!modal) {
      return;
    }

    activeModalTrigger = trigger;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    body.classList.add("modal-open");

    const focusableElements = findFocusableElements(modal);
    const preferredFocus = modal.querySelector(".popup-close") || focusableElements[0] || modal;

    if (!modal.hasAttribute("tabindex") && preferredFocus === modal) {
      modal.setAttribute("tabindex", "-1");
    }

    preferredFocus.focus();

    if (trigger === notificationButton) {
      playNotificationSound();
    }
  }

  function closeModal(modal) {
    if (!modal) {
      return;
    }

    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    body.classList.remove("modal-open");

    if (activeModalTrigger?.isConnected) {
      activeModalTrigger.focus();
    }

    activeModalTrigger = null;
  }

  function getOpenModal() {
    return document.querySelector(".popup-overlay.is-open");
  }

  function trapModalFocus(event, modal) {
    if (event.key !== "Tab") {
      return;
    }

    const focusableElements = findFocusableElements(modal);

    if (focusableElements.length === 0) {
      event.preventDefault();
      modal.focus();
      return;
    }

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    if (event.shiftKey && document.activeElement === firstElement) {
      event.preventDefault();
      lastElement.focus();
    } else if (!event.shiftKey && document.activeElement === lastElement) {
      event.preventDefault();
      firstElement.focus();
    }
  }

  function getCsrfToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
  }

  async function runAutomaticScan() {
    if (autoScanInFlight || document.hidden) {
      return;
    }

    autoScanInFlight = true;

    try {
      const response = await fetch("{% url 'run_network_scan' %}", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": getCsrfToken(),
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      if (!response.ok) {
        throw new Error(`Scan failed with status ${response.status}`);
      }

      window.location.reload();
    } catch (error) {
      console.error("Automatic scan failed", error);
      if (scanStatus) {
        scanStatus.textContent = "Automatic scan failed. The dashboard will try again later.";
      }
    } finally {
      autoScanInFlight = false;
    }
  }

  function startAutomaticScanning() {
    if (body.dataset.autoScan !== "true") {
      return;
    }

    const intervalSeconds = Number(body.dataset.interval);

    if (!Number.isFinite(intervalSeconds) || intervalSeconds <= 0) {
      console.warn("Automatic scan interval is invalid.");
      return;
    }

    window.setInterval(runAutomaticScan, intervalSeconds * 1000);
  }

  document.querySelectorAll("[data-modal-target]").forEach((trigger) => {
    trigger.addEventListener("click", () => openModal(trigger));
  });

  document.querySelectorAll(".popup-overlay").forEach((overlay) => {
    overlay.setAttribute("aria-hidden", "true");

    overlay.addEventListener("click", (event) => {
      if (event.target === overlay) {
        closeModal(overlay);
      }
    });
  });

  document.querySelectorAll(".popup-close").forEach((button) => {
    button.addEventListener("click", () => {
      closeModal(button.closest(".popup-overlay"));
    });
  });

  document.addEventListener("keydown", (event) => {
    const openModalElement = getOpenModal();

    if (!openModalElement) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeModal(openModalElement);
      return;
    }

    trapModalFocus(event, openModalElement);
  });

  document.querySelectorAll("[data-scan-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      const button = form.querySelector("[data-scan-button]");
      const label = form.querySelector("[data-scan-label]");

      if (button) {
        button.disabled = true;
        button.setAttribute("aria-busy", "true");
      }

      if (label) {
        label.textContent = "Scanning…";
      }

      if (scanStatus) {
        scanStatus.textContent = "Network scan started.";
      }
    });
  });

  prepareNotificationAlert();

  const releasePendingNotification = () => {
    if (pendingNotification) {
      playNotificationSound();
    }
  };

  window.addEventListener("pointerdown", releasePendingNotification, { once: true });
  window.addEventListener("keydown", releasePendingNotification, { once: true });

  startAutomaticScanning();
})();
