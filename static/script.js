/** @format */

let initialTime = 1500;
let time = initialTime;
let timerInterval = null;
let isRunning = false;

let isOnBreak = false;
let breakInterval = null;
let breakCount = 0;
let totalBreakTime = 0; // seconds

function updateTimerDisplay() {
  const minutes = Math.floor(time / 60);
  const seconds = time % 60;
  document.getElementById("timer").innerText = `${minutes}:${
    seconds < 10 ? "0" : ""
  }${seconds}`;
}

function startTimer() {
  if (isRunning || isOnBreak) return;

  isRunning = true;
  document.getElementById("status").innerText = "Studying";

  timerInterval = setInterval(() => {
    if (time > 0) {
      time--;
      updateTimerDisplay();
    } else {
      clearInterval(timerInterval);
      isRunning = false;
      document.getElementById("status").innerText = "Finished";
    }
  }, 1000);
}

function updateBreakDisplay() {
  document.getElementById("break-count").innerText = breakCount;
  document.getElementById("break-time").innerText = totalBreakTime;
}

function pauseTimer() {
  const breakBtn = document.getElementById("break-btn");
  const statusText = document.getElementById("status");

  // Case 1: study -> break
  if (isRunning && !isOnBreak) {
    isRunning = false;
    isOnBreak = true;

    clearInterval(timerInterval);

    breakCount += 1;
    updateBreakDisplay();

    statusText.innerText = "On Break";
    breakBtn.innerText = "Back to Study";

    breakInterval = setInterval(() => {
      totalBreakTime += 1;
      updateBreakDisplay();
    }, 1000);

    return;
  }

  // Case 2: break -> back to study
  if (isOnBreak) {
    isOnBreak = false;
    isRunning = true;

    clearInterval(breakInterval);

    statusText.innerText = "Studying";
    breakBtn.innerText = "Take Break";

    timerInterval = setInterval(() => {
      if (time > 0) {
        time--;
        updateTimerDisplay();
      } else {
        clearInterval(timerInterval);
        isRunning = false;
        statusText.innerText = "Finished";
      }
    }, 1000);
  }
}

function resetTimer() {
  clearInterval(timerInterval);
  clearInterval(breakInterval);

  isRunning = false;
  isOnBreak = false;

  time = 1500;
  breakCount = 0;
  totalBreakTime = 0;

  document.getElementById("status").innerText = "Idle";
  document.getElementById("break-btn").innerText = "Take Break";

  updateTimerDisplay();
  updateBreakDisplay();
}
async function saveSession() {
  console.log("save session");

  const duration = Math.floor((initialTime - time) / 60);
  const focusElement = document.getElementById("focus");
  const focus = focusElement ? focusElement.value : "High";

  console.log("Duration: ", duration)
  if (duration <= 0) {
    document.getElementById("feedback").innerText =
      "Please study for at least 1 minute before saving the session.";
    return;
  }

  try {
    const response = await fetch("/save_session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        duration: duration,
        breaks: breakCount,
        break_time: Math.floor(totalBreakTime / 60),
        focus_level: focus,
      }),
    });

    const data = await response.json();

    document.getElementById(
      "feedback"
    ).innerText = `${data.feedback} You earned ${data.points} points.`;

    await loadDashboard();
    await loadHistory();
    await loadWeeklyChart();

    resetTimer();
  } catch (error) {
    document.getElementById("feedback").innerText =
      "Error saving session. Please try again.";
    console.error("Save session error:", error);
  }
}

async function loadDashboard() {
  try {
    const response = await fetch("/get_dashboard");
    const data = await response.json();

    document.getElementById("total-time").innerText = data.total_time;
    document.getElementById("total-sessions").innerText = data.total_sessions;
    document.getElementById("total-points").innerText = data.total_points;
    document.getElementById("streak").innerText = data.streak;
  } catch (error) {
    console.error("Dashboard load error:", error);
  }
}

async function loadHistory() {
  console.log("Load history");
  try {
    const response = await fetch("/get_sessions");
    const data = await response.json();

    const history = document.getElementById("history");
    history.innerHTML = "";

    if (data.length === 0) {
      const li = document.createElement("li");
      li.innerText = "No study sessions recorded yet.";
      history.appendChild(li);
      return;
    }

    data.forEach((session) => {
      const li = document.createElement("li");
      li.innerText = `${session.date} | ${session.duration} mins | breaks: ${session.breaks} | focus: ${session.focus_level} | points: ${session.points}`;
      history.appendChild(li);
    });
  } catch (error) {
    console.error("History load error:", error);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  updateTimerDisplay();
  loadDashboard();
  loadHistory();
  loadWeeklyChart();
});

// ================= WEEKLY STUDY CHART =================

let weeklyChart = null;

async function loadWeeklyChart() {
  const response = await fetch("/get_weekly_stats");
  const data = await response.json();

  const canvas = document.getElementById("weeklyChart");

  if (!canvas) return;

  if (weeklyChart) {
    weeklyChart.destroy();
  }

  weeklyChart = new Chart(canvas, {
    type: "bar",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Study Time (minutes)",
          data: data.durations,
          backgroundColor: "rgba(75, 192, 192, 0.6)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 1,
          borderRadius: 5,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: "Minutes",
          },
        },
      },
    },
  });
}
