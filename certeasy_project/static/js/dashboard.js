// dashboard.js - API integration for CertEasy dashboard
document.addEventListener('DOMContentLoaded', function() {
  // Initialize dashboard components
  initializeDashboard();

  // Setup Alpine.js data if not already set up
  if (typeof window.Alpine !== 'undefined' && !window._dashboardDataInitialized) {
    window.Alpine.data('dashboardData', dashboardData);
    window._dashboardDataInitialized = true;
  }
});

function dashboardData() {
  return {
    userProfile: null,
    subscriptions: [],
    certifications: [],
    studyPlan: [],
    tasks: [],
    stats: {
      streak: 0,
      quizAverage: 0,
      tasksCompleted: 0,
      tasksTotal: 0
    },
    performanceData: [],
    notifications: [],
    isLoading: true,
    errorMessage: '',

    init() {
      this.loadDashboardData();
    },

    async loadDashboardData() {
      this.isLoading = true;
      try {
        // Load data in parallel for better performance
        await Promise.all([
          this.loadUserProfile(),
          this.loadSubscriptions(),
          this.loadCertifications(),
          this.loadStudyPlan(),
          this.loadNotifications(),
          this.loadStats()
        ]);

        // Initialize charts after data is loaded
        this.initializeCharts();

      } catch (error) {
        console.error('Error loading dashboard data:', error);
        this.errorMessage = 'Failed to load dashboard data. Please refresh the page.';
      } finally {
        this.isLoading = false;
      }
    },

    async loadUserProfile() {
      try {
        const response = await fetchWithAuth('/api/accounts/profile/');
        this.userProfile = response;
      } catch (error) {
        console.error('Error loading user profile:', error);
      }
    },

    async loadSubscriptions() {
      try {
        const response = await fetchWithAuth('/api/accounts/subscriptions/');
        this.subscriptions = response;
      } catch (error) {
        console.error('Error loading subscriptions:', error);
      }
    },

    async loadCertifications() {
      try {
        const response = await fetchWithAuth('/api/certifications/');
        this.certifications = response;

        // Update certification progress stats
        if (this.certifications.length > 0) {
          this.stats.overallProgress = this.calculateOverallProgress();
        }
      } catch (error) {
        console.error('Error loading certifications:', error);
      }
    },

    async loadStudyPlan() {
      // This would integrate with a study plan API endpoint if you have one
      // For now, we'll simulate with certifications data
      try {
        const certifications = await fetchWithAuth('/api/certifications/');

        // Create study plan items based on certifications
        this.studyPlan = certifications.slice(0, 3).map((cert, index) => {
          const timeSlots = ['8:00 AM', '10:30 AM', '2:00 PM'];
          const durations = ['45 minutes', '60 minutes', '90 minutes'];
          const activities = ['Flashcards and practice questions', 'Interactive exercises', 'Video lesson and notes'];
          const statuses = ['Completed', 'In Progress', 'Upcoming'];

          return {
            id: cert.id,
            title: cert.title,
            time: timeSlots[index],
            duration: durations[index],
            activity: activities[index],
            status: statuses[index]
          };
        });

        // Count tasks for today
        this.tasks = this.studyPlan;
        this.stats.tasksTotal = this.tasks.length;
        this.stats.tasksCompleted = this.tasks.filter(task => task.status === 'Completed').length;
      } catch (error) {
        console.error('Error creating study plan:', error);
      }
    },

    async loadNotifications() {
      // Placeholder for notification API endpoint
      // This would connect to a notifications API if available
      this.notifications = [
        {
          id: 1,
          title: 'New flashcards added for GRE',
          time: '2 hours ago',
          type: 'resource',
          icon: 'book-open'
        },
        {
          id: 2,
          title: 'CFA Level I exam schedule released',
          time: 'Yesterday',
          type: 'calendar',
          icon: 'calendar'
        },
        {
          id: 3,
          title: 'Join your study room now',
          time: '2 days ago',
          type: 'community',
          icon: 'users'
        }
      ];
    },

    async loadStats() {
      try {
        // Calculate quiz averages using real data if available
        const flashcardsResponse = await fetchWithAuth('/api/flashcards/');

        // Sample streak calculation
        // This would ideally come from a user activity log API
        this.stats.streak = 14;

        // Calculate quiz average from available data
        // You would likely have a dedicated API endpoint for this
        const quizData = [85, 76, 92, 78, 81];
        this.stats.quizAverage = quizData.reduce((a, b) => a + b, 0) / quizData.length;

        // Performance data for chart
        this.performanceData = [78, 82, 75, 85, 90, 82, 88];
      } catch (error) {
        console.error('Error loading stats:', error);
      }
    },

    calculateOverallProgress() {
      if (!this.certifications.length) return 0;

      const totalProgress = this.certifications.reduce((sum, cert) => sum + cert.progress, 0);
      return Math.round(totalProgress / this.certifications.length);
    },

    initializeCharts() {
      // Initialize performance chart
      const ctx = document.getElementById('performanceChart');
      if (ctx) {
        const performanceChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
              data: this.performanceData,
              borderColor: '#3B82F6',
              backgroundColor: 'rgba(59, 130, 246, 0.1)',
              borderWidth: 2,
              tension: 0.4,
              pointRadius: 0
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                enabled: false
              }
            },
            scales: {
              x: {
                display: false
              },
              y: {
                display: false,
                min: 50,
                max: 100
              }
            }
          }
        });
      }
    }
  };
}

// Helper function for authenticated API fetches
async function fetchWithAuth(url, options = {}) {
  // Get CSRF token from cookie
  const csrfToken = getCookie('csrftoken');

  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken
    },
    credentials: 'same-origin'  // Include cookies with the request
  };

  const response = await fetch(url, { ...defaultOptions, ...options });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: `API request failed with status ${response.status}`
    }));
    throw new Error(error.detail || 'Unknown error occurred');
  }

  return response.json();
}

// Initialize dashboard components
function initializeDashboard() {
  // This function can handle any one-time setup that needs to happen
  setupContinueLearningButton();
  setupNotificationHandlers();
  setupProfileMenu();
}

function setupContinueLearningButton() {
  const continueBtn = document.querySelector('button:contains("Continue Learning")');
  if (continueBtn) {
    continueBtn.addEventListener('click', async () => {
      try {
        const response = await fetchWithAuth('/api/certifications/');
        if (response.length > 0) {
          // Find certification with highest progress that's not complete
          const inProgressCerts = response.filter(cert => cert.progress > 0 && cert.progress < 100);
          if (inProgressCerts.length > 0) {
            // Sort by progress descending
            inProgressCerts.sort((a, b) => b.progress - a.progress);
            // Redirect to the most progressed certification
            window.location.href = `/certifications/${inProgressCerts[0].id}/`;
          } else {
            // If no in-progress certs, go to first cert
            window.location.href = `/certifications/${response[0].id}/`;
          }
        }
      } catch (error) {
        console.error('Error continuing learning:', error);
      }
    });
  }
}

function setupNotificationHandlers() {
  // Mark notifications as read when clicked
  const notificationItems = document.querySelectorAll('.notification-item');
  notificationItems.forEach(item => {
    item.addEventListener('click', async (e) => {
      const notificationId = item.dataset.id;
      try {
        // This would call your notification read API
        await fetchWithAuth(`/api/notifications/${notificationId}/read/`, {
          method: 'POST'
        });
        // Update UI to show notification as read
        item.classList.add('opacity-50');
      } catch (error) {
        console.error('Error marking notification as read:', error);
      }
    });
  });
}

function setupProfileMenu() {
  // This is handled by Alpine.js in your HTML
}

// Helper function to get cookies (for CSRF token)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
