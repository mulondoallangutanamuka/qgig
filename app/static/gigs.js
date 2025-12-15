// Gig management functions

async function loadGigs(urgentOnly = false) {
    const gigsList = document.getElementById('gigsList');
    gigsList.innerHTML = '<p>Loading gigs...</p>';
    
    try {
        const url = urgentOnly ? `${API_URL}/jobs?urgent=true` : `${API_URL}/jobs`;
        const response = await fetch(url);
        const data = await response.json();
        
        if (response.ok && data.gigs && data.gigs.length > 0) {
            gigsList.innerHTML = data.gigs.map(gig => `
                <div class="gig-card ${gig.is_urgent ? 'urgent' : ''}">
                    <div class="gig-header">
                        <h3 class="gig-title">${gig.title}</h3>
                        <span class="gig-badge ${gig.status}">${gig.status.toUpperCase()}</span>
                    </div>
                    <p>${gig.description}</p>
                    <div class="gig-details">
                        <div class="gig-detail">
                            <span class="gig-detail-label">Location</span>
                            <span class="gig-detail-value">${gig.location}</span>
                        </div>
                        <div class="gig-detail">
                            <span class="gig-detail-label">Payment</span>
                            <span class="gig-detail-value">KES ${gig.pay_amount}</span>
                        </div>
                        ${gig.duration_hours ? `
                        <div class="gig-detail">
                            <span class="gig-detail-label">Duration</span>
                            <span class="gig-detail-value">${gig.duration_hours} hours</span>
                        </div>
                        ` : ''}
                        <div class="gig-detail">
                            <span class="gig-detail-label">Institution</span>
                            <span class="gig-detail-value">${gig.institution.name}</span>
                        </div>
                    </div>
                    ${gig.is_urgent ? '<p style="color: #e74c3c; font-weight: 600;">🔥 URGENT</p>' : ''}
                    <div class="gig-actions">
                        <button class="btn btn-primary" onclick="expressInterest(${gig.id})">Express Interest</button>
                    </div>
                </div>
            `).join('');
        } else {
            gigsList.innerHTML = '<p>No gigs available at the moment.</p>';
        }
    } catch (error) {
        gigsList.innerHTML = '<p>Error loading gigs. Please try again.</p>';
    }
}

async function expressInterest(gigId) {
    try {
        const response = await fetch(`${API_URL}/jobs/${gigId}/express-interest`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        if (response.ok) {
            alert(data.message || 'Interest expressed successfully!');
            loadGigs(false);
        } else {
            alert(data.error || 'Failed to express interest');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

async function loadMyGigs() {
    const myGigsList = document.getElementById('myGigsList');
    myGigsList.innerHTML = '<p>Loading your gigs...</p>';
    
    try {
        const response = await fetch(`${API_URL}/jobs/my-gigs`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        
        if (response.ok && data.gigs && data.gigs.length > 0) {
            myGigsList.innerHTML = data.gigs.map(gig => `
                <div class="gig-card ${gig.is_urgent ? 'urgent' : ''}">
                    <div class="gig-header">
                        <h3 class="gig-title">${gig.title}</h3>
                        <span class="gig-badge ${gig.status}">${gig.status.toUpperCase()}</span>
                    </div>
                    <div class="gig-details">
                        <div class="gig-detail">
                            <span class="gig-detail-label">Location</span>
                            <span class="gig-detail-value">${gig.location}</span>
                        </div>
                        <div class="gig-detail">
                            <span class="gig-detail-label">Payment</span>
                            <span class="gig-detail-value">KES ${gig.pay_amount}</span>
                        </div>
                        <div class="gig-detail">
                            <span class="gig-detail-label">Interested</span>
                            <span class="gig-detail-value">${gig.interest_count} professionals</span>
                        </div>
                        ${gig.assigned_to ? `<div class="gig-detail"><span class="gig-detail-label">Assigned To</span><span class="gig-detail-value">${gig.assigned_to}</span></div>` : ''}
                    </div>
                    <div class="gig-actions">
                        ${gig.status === 'open' ? `<button class="btn btn-secondary" onclick="viewInterestedProfessionals(${gig.id})">View Interested (${gig.interest_count})</button>` : ''}
                        ${gig.status === 'assigned' ? `<button class="btn btn-primary" onclick="initiatePayment(${gig.id})">Pay Professional</button>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            myGigsList.innerHTML = '<p>You haven\'t posted any gigs yet.</p>';
        }
    } catch (error) {
        myGigsList.innerHTML = '<p>Error loading gigs. Please try again.</p>';
    }
}

async function handlePostGig(event) {
    event.preventDefault();
    const errorDiv = document.getElementById('gigError');
    const successDiv = document.getElementById('gigSuccess');
    errorDiv.classList.remove('show');
    successDiv.classList.remove('show');
    
    const gigData = {
        title: document.getElementById('gigTitle').value,
        description: document.getElementById('gigDescription').value,
        location: document.getElementById('gigLocation').value,
        pay_amount: parseFloat(document.getElementById('gigPayAmount').value),
        duration_hours: parseFloat(document.getElementById('gigDuration').value) || null,
        is_urgent: document.getElementById('gigUrgent').checked
    };
    
    try {
        const response = await fetch(`${API_URL}/jobs`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify(gigData)
        });
        const data = await response.json();
        if (response.ok) {
            successDiv.textContent = 'Gig posted successfully!';
            successDiv.classList.add('show');
            document.getElementById('postGigForm').reset();
            setTimeout(() => showPage('myGigs'), 2000);
        } else {
            errorDiv.textContent = data.error || 'Failed to post gig';
            errorDiv.classList.add('show');
        }
    } catch (error) {
        errorDiv.textContent = 'Network error. Please try again.';
        errorDiv.classList.add('show');
    }
}

async function viewInterestedProfessionals(gigId) {
    try {
        const response = await fetch(`${API_URL}/jobs/${gigId}/interested-professionals`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        if (response.ok && data.interested_professionals && data.interested_professionals.length > 0) {
            const profList = data.interested_professionals.map(prof => 
                `ID: ${prof.id} - ${prof.name} - ${prof.skills || 'No skills'} - Rate: KES ${prof.hourly_rate || 'N/A'}/hr`
            ).join('\n');
            const profId = prompt(`Interested Professionals:\n\n${profList}\n\nEnter professional ID to assign:`);
            if (profId) assignGig(gigId, profId);
        } else {
            alert('No professionals have expressed interest yet.');
        }
    } catch (error) {
        alert('Error loading interested professionals.');
    }
}

async function assignGig(gigId, professionalId) {
    try {
        const response = await fetch(`${API_URL}/jobs/${gigId}/assign/${professionalId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        const data = await response.json();
        if (response.ok) {
            alert(data.message || 'Gig assigned successfully!');
            loadMyGigs();
        } else {
            alert(data.error || 'Failed to assign gig');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}

async function initiatePayment(gigId) {
    if (!confirm('Proceed to payment for this gig?')) return;
    try {
        const response = await fetch(`${API_URL}/payments/initiate`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ gig_id: gigId })
        });
        const data = await response.json();
        if (response.ok) {
            alert('Payment initiated! You will be redirected to PesaPal.');
            if (data.redirect_url) window.open(data.redirect_url, '_blank');
            loadMyGigs();
        } else {
            alert(data.error || 'Failed to initiate payment');
        }
    } catch (error) {
        alert('Network error. Please try again.');
    }
}
