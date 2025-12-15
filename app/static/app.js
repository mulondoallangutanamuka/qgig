const API_URL = 'http://127.0.0.1:5000';
let currentUser = null;
let authToken = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Check if user is authenticated
function checkAuth() {
    authToken = localStorage.getItem('authToken');
    const userStr = localStorage.getItem('currentUser');
    
    if (authToken && userStr) {
        currentUser = JSON.parse(userStr);
        updateNavigation(true);
    } else {
        updateNavigation(false);
    }
}

// Update navigation based on auth state
function updateNavigation(isAuthenticated) {
    const navLogin = document.getElementById('navLogin');
    const navRegister = document.getElementById('navRegister');
    const navProfile = document.getElementById('navProfile');
    const navLogout = document.getElementById('navLogout');
    const navGigs = document.getElementById('navGigs');
    const navMyGigs = document.getElementById('navMyGigs');
    
    if (isAuthenticated) {
        navLogin.style.display = 'none';
        navRegister.style.display = 'none';
        navProfile.style.display = 'block';
        navLogout.style.display = 'block';
        
        if (currentUser.role === 'professional') {
            navGigs.style.display = 'block';
            navMyGigs.style.display = 'none';
        } else if (currentUser.role === 'institution') {
            navGigs.style.display = 'none';
            navMyGigs.style.display = 'block';
        }
    } else {
        navLogin.style.display = 'block';
        navRegister.style.display = 'block';
        navProfile.style.display = 'none';
        navLogout.style.display = 'none';
        navGigs.style.display = 'none';
        navMyGigs.style.display = 'none';
    }
}

// Show page
function showPage(pageName) {
    const pages = document.querySelectorAll('.page');
    pages.forEach(page => page.classList.remove('active'));
    
    const targetPage = document.getElementById(pageName + 'Page');
    if (targetPage) {
        targetPage.classList.add('active');
        
        // Load profile data if showing profile page
        if (pageName === 'profile' && currentUser) {
            loadProfileData();
        }
    }
}

// Handle registration
async function handleRegister(event) {
    event.preventDefault();
    
    const email = document.getElementById('registerEmail').value;
    const password = document.getElementById('registerPassword').value;
    const role = document.getElementById('registerRole').value;
    
    const errorDiv = document.getElementById('registerError');
    const successDiv = document.getElementById('registerSuccess');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password, role })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            successDiv.textContent = 'Registration successful! Please login.';
            successDiv.classList.add('show');
            document.getElementById('registerForm').reset();
            setTimeout(() => showPage('login'), 2000);
        } else {
            errorDiv.textContent = data.error || 'Registration failed';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.classList.add('show');
    }
}

// Handle login
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    const errorDiv = document.getElementById('loginError');
    const successDiv = document.getElementById('loginSuccess');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    try {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            authToken = data.token;
            currentUser = data.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            successDiv.textContent = 'Login successful!';
            successDiv.classList.add('show');
            
            updateNavigation(true);
            document.getElementById('loginForm').reset();
            
            setTimeout(() => showPage('profile'), 1000);
        } else {
            errorDiv.textContent = data.error || 'Login failed';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.classList.add('show');
    }
}

// Logout
function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    authToken = null;
    currentUser = null;
    updateNavigation(false);
    showPage('home');
}

// Load profile data
async function loadProfileData() {
    const userInfoDiv = document.getElementById('userInfo');
    const profForm = document.getElementById('professionalProfileForm');
    const instForm = document.getElementById('institutionProfileForm');
    
    // Show user info
    userInfoDiv.innerHTML = `
        <p><strong>Email:</strong> ${currentUser.email}</p>
        <p><strong>Role:</strong> ${currentUser.role}</p>
    `;
    
    // Show appropriate profile form
    if (currentUser.role === 'professional') {
        profForm.style.display = 'block';
        instForm.style.display = 'none';
        await loadProfessionalProfile();
    } else if (currentUser.role === 'institution') {
        profForm.style.display = 'none';
        instForm.style.display = 'block';
        await loadInstitutionProfile();
    }
}

// Load professional profile
async function loadProfessionalProfile() {
    try {
        const response = await fetch(`${API_URL}/professional/profile`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const profile = await response.json();
            document.getElementById('profFullName').value = profile.full_name || '';
            document.getElementById('profPhone').value = profile.phone || '';
            document.getElementById('profBio').value = profile.bio || '';
            document.getElementById('profSkills').value = profile.skills || '';
            document.getElementById('profHourlyRate').value = profile.hourly_rate || '';
            document.getElementById('profDailyRate').value = profile.daily_rate || '';
            document.getElementById('profLocation').value = profile.location || '';
        }
    } catch (error) {
        console.log('No existing profile');
    }
}

// Load institution profile
async function loadInstitutionProfile() {
    try {
        const response = await fetch(`${API_URL}/institution/profile`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const profile = await response.json();
            document.getElementById('instName').value = profile.institution_name || '';
            document.getElementById('instContactPerson').value = profile.contact_person || '';
            document.getElementById('instPhone').value = profile.phone || '';
            document.getElementById('instEmail').value = profile.email || '';
            document.getElementById('instAddress').value = profile.address || '';
            document.getElementById('instDescription').value = profile.description || '';
            document.getElementById('instWebsite').value = profile.website || '';
        }
    } catch (error) {
        console.log('No existing profile');
    }
}

// Handle professional profile
async function handleProfessionalProfile(event) {
    event.preventDefault();
    
    const errorDiv = document.getElementById('profError');
    const successDiv = document.getElementById('profSuccess');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    const profileData = {
        full_name: document.getElementById('profFullName').value,
        phone: document.getElementById('profPhone').value,
        bio: document.getElementById('profBio').value,
        skills: document.getElementById('profSkills').value,
        hourly_rate: parseFloat(document.getElementById('profHourlyRate').value) || null,
        daily_rate: parseFloat(document.getElementById('profDailyRate').value) || null,
        location: document.getElementById('profLocation').value
    };
    
    try {
        // Try to update first
        let response = await fetch(`${API_URL}/professional/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        // If profile doesn't exist, create it
        if (response.status === 404) {
            response = await fetch(`${API_URL}/professional/profile`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            successDiv.textContent = data.message || 'Profile saved successfully!';
            successDiv.classList.add('show');
        } else {
            errorDiv.textContent = data.error || 'Failed to save profile';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.classList.add('show');
    }
}

// Handle institution profile
async function handleInstitutionProfile(event) {
    event.preventDefault();
    
    const errorDiv = document.getElementById('instError');
    const successDiv = document.getElementById('instSuccess');
    
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    const profileData = {
        institution_name: document.getElementById('instName').value,
        contact_person: document.getElementById('instContactPerson').value,
        phone: document.getElementById('instPhone').value,
        email: document.getElementById('instEmail').value,
        address: document.getElementById('instAddress').value,
        description: document.getElementById('instDescription').value,
        website: document.getElementById('instWebsite').value
    };
    
    try {
        // Try to update first
        let response = await fetch(`${API_URL}/institution/profile`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        // If profile doesn't exist, create it
        if (response.status === 404) {
            response = await fetch(`${API_URL}/institution/profile`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            successDiv.textContent = data.message || 'Profile saved successfully!';
            successDiv.classList.add('show');
        } else {
            errorDiv.textContent = data.error || 'Failed to save profile';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.classList.add('show');
    }
}
