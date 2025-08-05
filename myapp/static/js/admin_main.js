// Sidebar toggle
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const toggleBtn = document.getElementById('sidebarToggle');

toggleBtn?.addEventListener('click', () => {
  sidebar.classList.toggle('show');
  sidebar.classList.toggle('collapsed');
  mainContent.classList.toggle('collapsed');
  toggleBtn.classList.toggle('collapsed');
});

// Logout confirmation
document.getElementById('logout-link')?.addEventListener('click', function (event) {
  event.preventDefault();
  if (confirm('Are you sure you want to logout?')) {
    document.getElementById('logout-form').submit();
  }
});

document.getElementById('dropdownLogoutButton')?.addEventListener('click', function (event) {
  event.preventDefault();
  if (confirm('Are you sure you want to logout?')) {
    document.getElementById('dropdown-logout-form').submit();
  }
});

// ---------------------- SOUND TOGGLE ----------------------
let soundEnabled = localStorage.getItem("soundEnabled") !== "false"; // default: true
const toggleSoundBtn = document.getElementById("toggleSoundBtn");
const soundIcon = document.getElementById("soundIcon");
const notifSound = document.getElementById("notifSound");

function updateSoundUI() {
  if (soundEnabled) {
    soundIcon.className = "fas fa-volume-up";
    toggleSoundBtn.classList.remove("btn-outline-danger");
    toggleSoundBtn.classList.add("btn-outline-secondary");
  } else {
    soundIcon.className = "fas fa-volume-mute";
    toggleSoundBtn.classList.remove("btn-outline-secondary");
    toggleSoundBtn.classList.add("btn-outline-danger");
  }
}

toggleSoundBtn?.addEventListener("click", () => {
  soundEnabled = !soundEnabled;
  localStorage.setItem("soundEnabled", soundEnabled);
  updateSoundUI();
});

updateSoundUI(); // Initial UI setup

function playNotificationSound() {
  if (soundEnabled && notifSound) {
    notifSound.play().catch(err => console.warn("Sound play failed:", err));
  }
}

// ---------------------- NOTIFICATION BELL ----------------------
document.addEventListener('DOMContentLoaded', function () {
  let lastChecked = new Date().toISOString();
  const notifBadge = document.getElementById('notificationBadge');
  const notifDropdown = document.getElementById('notifDropdown');
  const noNotifItem = document.getElementById('noNotifItem');
  const bell = document.getElementById('notificationBell');
  const bellIcon = document.querySelector('#notificationBell i');

  function createNotifItem(message, type) {
    const li = document.createElement('li');
    li.className = `dropdown-item small text-${type}`;
    li.innerHTML = `<i class="fas fa-info-circle me-2"></i> ${message}`;
    return li;
  }

  function pollNotifications() {
    fetch(`/check-new-reservations/?last_checked=${lastChecked}`)
      .then(response => response.json())
      .then(data => {
        if (data.notifications && data.notifications.length > 0) {
          notifBadge.textContent = data.notifications.length;
          notifBadge.style.display = 'inline-block';
          bellIcon.classList.add('fa-shake');
          noNotifItem?.classList.add('d-none');

          // Clear old notifications
          notifDropdown.querySelectorAll('.dropdown-item.text-success, .dropdown-item.text-warning, .dropdown-item.text-danger')
            .forEach(e => e.remove());

          // Add new notifications
          data.notifications.forEach(n => {
            let typeColor = 'secondary';
            if (n.type === 'new') typeColor = 'success';
            if (n.type === 'updated') typeColor = 'warning';
            if (n.type === 'canceled') typeColor = 'danger';
            notifDropdown.insertBefore(createNotifItem(n.message, typeColor), noNotifItem);
          });

          playNotificationSound();
        }
        lastChecked = new Date().toISOString();
      });
  }

  bell?.addEventListener('click', () => {
    bellIcon.classList.remove('fa-shake');
    notifBadge.style.display = 'none';
    notifBadge.textContent = '';
  });

  setInterval(pollNotifications, 10000); // every 10 seconds
});
