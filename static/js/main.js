// Main JavaScript for LMS Application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar toggle
    initSidebar();
    
    // Initialize dark mode toggle
    initDarkMode();
    
    // Initialize tooltips
    initTooltips();
    
    // Initialize form validation
    initFormValidation();
    
    // Initialize code editor if present
    initCodeEditor();
    
    // Initialize chatbot if present
    initChatbot();
});

// Sidebar toggle functionality
function initSidebar() {
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    if (!sidebarToggle) return;
    
    const sidebar = document.querySelector('.sidebar');
    const content = document.querySelector('.content');
    
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('sidebar-collapsed');
        content.classList.toggle('content-full');
        sidebarToggle.classList.toggle('collapsed');
        
        // Save preference to localStorage
        const isCollapsed = sidebar.classList.contains('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', isCollapsed);
    });
    
    // Check localStorage for saved preference
    const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('sidebar-collapsed');
        content.classList.add('content-full');
        sidebarToggle.classList.add('collapsed');
    }
}

// Dark mode toggle functionality
function initDarkMode() {
    const darkModeToggle = document.querySelector('.dark-mode-toggle');
    if (!darkModeToggle) return;
    
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        
        // Save preference to localStorage
        const isDarkMode = document.body.classList.contains('dark-mode');
        localStorage.setItem('dark-mode', isDarkMode);
        
        // Update icon
        const icon = darkModeToggle.querySelector('i');
        if (isDarkMode) {
            icon.classList.replace('fa-moon', 'fa-sun');
        } else {
            icon.classList.replace('fa-sun', 'fa-moon');
        }
    });
    
    // Check localStorage for saved preference
    const isDarkMode = localStorage.getItem('dark-mode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        const icon = darkModeToggle.querySelector('i');
        if (icon) {
            icon.classList.replace('fa-moon', 'fa-sun');
        }
    }
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const text = this.getAttribute('data-tooltip');
            const tooltipEl = document.createElement('div');
            tooltipEl.classList.add('tooltip');
            tooltipEl.textContent = text;
            
            document.body.appendChild(tooltipEl);
            
            const rect = this.getBoundingClientRect();
            tooltipEl.style.top = rect.bottom + 10 + 'px';
            tooltipEl.style.left = rect.left + (rect.width / 2) - (tooltipEl.offsetWidth / 2) + 'px';
            
            setTimeout(() => {
                tooltipEl.classList.add('show');
            }, 10);
        });
        
        tooltip.addEventListener('mouseleave', function() {
            const tooltipEl = document.querySelector('.tooltip');
            if (tooltipEl) {
                tooltipEl.classList.remove('show');
                setTimeout(() => {
                    tooltipEl.remove();
                }, 300);
            }
        });
    });
}

// Form validation
function initFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

// Code editor functionality
function initCodeEditor() {
    const codeEditors = document.querySelectorAll('.code-editor-content');
    if (codeEditors.length === 0) return;
    
    codeEditors.forEach(editor => {
        // Add line numbers
        editor.addEventListener('input', function() {
            const lines = this.value.split('\n').length;
            const lineNumbers = this.previousElementSibling;
            if (lineNumbers && lineNumbers.classList.contains('code-editor-line-numbers')) {
                let numbersHTML = '';
                for (let i = 1; i <= lines; i++) {
                    numbersHTML += i + '<br>';
                }
                lineNumbers.innerHTML = numbersHTML;
            }
        });
        
        // Trigger initial line numbers
        const event = new Event('input');
        editor.dispatchEvent(event);
        
        // Tab key handling
        editor.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                e.preventDefault();
                
                const start = this.selectionStart;
                const end = this.selectionEnd;
                
                this.value = this.value.substring(0, start) + '    ' + this.value.substring(end);
                
                this.selectionStart = this.selectionEnd = start + 4;
            }
        });
    });
    
    // Run code button
    const runButtons = document.querySelectorAll('.code-editor-run');
    runButtons.forEach(button => {
        button.addEventListener('click', function() {
            const editorContent = this.closest('.code-editor').querySelector('.code-editor-content');
            const code = editorContent.value;
            const outputElement = this.closest('.code-editor').nextElementSibling;
            
            if (outputElement && outputElement.classList.contains('code-output')) {
                // Send code to backend for execution
                fetch('/api/execute-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ code: code }),
                })
                .then(response => response.json())
                .then(data => {
                    outputElement.textContent = data.output;
                })
                .catch(error => {
                    outputElement.textContent = 'Error: ' + error.message;
                });
            }
        });
    });
}

// Chatbot functionality
function initChatbot() {
    const chatbotContainer = document.querySelector('.chatbot-container');
    if (!chatbotContainer) return;
    
    const messageInput = document.querySelector('.chatbot-input-field');
    const sendButton = document.querySelector('.chatbot-input-button');
    const messagesContainer = document.querySelector('.chatbot-messages');
    
    // Send message function
    function sendMessage() {
        const message = messageInput.value.trim();
        if (message === '') return;
        
        // Add user message to UI
        addMessage(message, true);
        
        // Clear input
        messageInput.value = '';
        
        // Get session ID
        const sessionId = chatbotContainer.getAttribute('data-session-id');
        
        // Send message to backend
        fetch('/api/chatbot/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                message: message
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Add AI response to UI
            addMessage(data.ai_message.content, false);
            
            // Scroll to bottom
            scrollToBottom();
        })
        .catch(error => {
            console.error('Error:', error);
            addMessage('Sorry, there was an error processing your request.', false);
        });
    }
    
    // Add message to UI
    function addMessage(content, isUser) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chatbot-message');
        messageElement.classList.add(isUser ? 'chatbot-message-user' : 'chatbot-message-ai');
        
        const contentElement = document.createElement('div');
        contentElement.classList.add('chatbot-message-content');
        contentElement.textContent = content;
        
        const timeElement = document.createElement('div');
        timeElement.classList.add('chatbot-message-time');
        
        const now = new Date();
        timeElement.textContent = now.getHours().toString().padStart(2, '0') + ':' + 
                                 now.getMinutes().toString().padStart(2, '0');
        
        messageElement.appendChild(contentElement);
        messageElement.appendChild(timeElement);
        
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        scrollToBottom();
    }
    
    // Scroll messages to bottom
    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Event listeners
    if (sendButton) {
        sendButton.addEventListener('click', sendMessage);
    }
    
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Session switching
    const sessionItems = document.querySelectorAll('.chatbot-session');
    sessionItems.forEach(item => {
        item.addEventListener('click', function() {
            const sessionId = this.getAttribute('data-session-id');
            
            // Update active session
            sessionItems.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            
            // Update session ID
            chatbotContainer.setAttribute('data-session-id', sessionId);
            
            // Clear messages
            messagesContainer.innerHTML = '';
            
            // Load messages for this session
            fetch(`/api/chatbot/session/${sessionId}/messages`)
                .then(response => response.json())
                .then(data => {
                    data.messages.forEach(message => {
                        addMessage(message.content, message.is_user);
                    });
                    
                    // Scroll to bottom
                    scrollToBottom();
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        });
    });
    
    // Initial scroll to bottom
    scrollToBottom();
}

// Lesson completion functionality
function markLessonComplete(lessonId) {
    fetch(`/student/lesson/${lessonId}/complete`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && data.success) {
            // Update UI to show lesson is completed
            const completeButton = document.querySelector('.mark-complete-button');
            if (completeButton) {
                completeButton.textContent = 'Completed';
                completeButton.disabled = true;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Course enrollment functionality
function enrollInCourse(courseId) {
    fetch(`/student/enroll/${courseId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            return response.json();
        }
    })
    .then(data => {
        if (data && data.success) {
            // Update UI to show enrollment
            const enrollButton = document.querySelector(`.enroll-button[data-course-id="${courseId}"]`);
            if (enrollButton) {
                enrollButton.textContent = 'Enrolled';
                enrollButton.disabled = true;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Flash message auto-dismiss
setTimeout(() => {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        message.style.opacity = '0';
        setTimeout(() => {
            message.remove();
        }, 300);
    });
}, 5000);

// Progress tracking
function updateProgress(courseId, lessonId) {
    fetch(`/courses/${courseId}/progress`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `lesson_id=${lessonId}`
    })
    .then(response => response.json())
    .then(data => {
        // Update progress bar if it exists
        const progressBar = document.querySelector(`.course-${courseId} .progress-bar`);
        if (progressBar && data.progress) {
            progressBar.style.width = `${data.progress}%`;
        }
    })
    .catch(error => console.error('Error updating progress:', error));
}

// Notifications
function showNotification(message, type = 'info') {
    const notificationArea = document.getElementById('notification-area');
    if (notificationArea) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', function() {
            notification.remove();
        });
        
        notification.appendChild(closeBtn);
        notificationArea.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('notification-hiding');
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }
}

// Language switcher (for multilingual support)
function switchLanguage(lang) {
    fetch(`/switch-language/${lang}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload page to apply language change
            window.location.reload();
        }
    })
    .catch(error => console.error('Error switching language:', error));
} 