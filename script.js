document.addEventListener('DOMContentLoaded', () => {
    const onboardingModalBackdrop = document.getElementById('onboarding-modal-backdrop');
    const onboardingModal = document.getElementById('onboarding-modal');
    const createFeedBtn = document.getElementById('create-feed-btn');
    const modalContent = document.querySelector('.modal-content');
    const loadingState = document.querySelector('.loading-state');
    const studyFieldInput = document.getElementById('study-field');
    const careerGoalInput = document.getElementById('career-goal');

    const userProfileDisplay = document.getElementById('user-profile');
    const displayStudy = document.getElementById('display-study');
    const displayCareer = document.getElementById('display-career');
    const editChoicesBtn = document.getElementById('edit-choices');

    const opportunitiesGrid = document.getElementById('opportunities-grid');
    const emptyState = document.getElementById('empty-state');

    createFeedBtn.addEventListener('click', () => {
        const studyField = studyFieldInput.value.trim();
        const careerGoal = careerGoalInput.value.trim();

        if (studyField && careerGoal) {
            // Show loading state
            modalContent.style.display = 'none';
            loadingState.style.display = 'block';

            // Simulate a network request
            setTimeout(() => {
                // Hide modal and show main app
                onboardingModalBackdrop.style.display = 'none';
                
                // Update user profile display
                displayStudy.textContent = studyField;
                displayCareer.textContent = careerGoal;
                userProfileDisplay.style.display = 'flex';

                // Populate feed with dummy data
                populateOpportunities(careerGoal);

            }, 2000);
        } else {
            alert('Please fill out both fields.');
        }
    });

    editChoicesBtn.addEventListener('click', () => {
        onboardingModalBackdrop.style.display = 'flex';
        modalContent.style.display = 'block';
        loadingState.style.display = 'none';
    });

    function populateOpportunities(careerGoal) {
        // Clear existing opportunities
        opportunitiesGrid.innerHTML = '';

        // Dummy data for demonstration
        const opportunities = [
            {
                organization: 'Innovate Corp',
                title: 'AI/ML Engineering Internship',
                summary: 'Join our team to work on cutting-edge machine learning models that power our recommendation engine.',
                tags: ['Internship', 'AI/ML', 'Remote'],
                recommended: true
            },
            {
                organization: 'DesignHub',
                title: 'UX/UI Designer for Mobile App',
                summary: 'We are looking for a creative UX/UI designer to redesign our flagship mobile application.',
                tags: ['Full-Time', 'UX Design', 'On-site'],
                recommended: false
            },
            {
                organization: 'Future Leaders Foundation',
                title: 'Tech Leadership Grant',
                summary: 'A grant for aspiring tech leaders to fund their innovative projects and ideas.',
                tags: ['Grant', 'Leadership', 'Tech'],
                recommended: true
            }
        ];

        if (opportunities.length > 0) {
            emptyState.style.display = 'none';
            opportunities.forEach(opp => {
                const card = document.createElement('div');
                card.className = 'opportunity-card';
                card.onclick = () => window.open('https://example.com', '_blank');

                let badgeHtml = '';
                if (opp.recommended) {
                    badgeHtml = `
                        <div class="recommend-badge">
                            Recommended
                            <span class="tooltip">Recommended because you're interested in ${careerGoal}.</span>
                        </div>
                    `;
                }

                card.innerHTML = `
                    ${badgeHtml}
                    <div class="card-header">${opp.organization}</div>
                    <h3 class="card-title">${opp.title}</h3>
                    <div class="ai-summary">
                        <div class="label">AI Summary</div>
                        <p>${opp.summary}</p>
                    </div>
                    <div class="tags-section">
                        ${opp.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                `;
                opportunitiesGrid.appendChild(card);
            });
        } else {
            emptyState.style.display = 'block';
        }
    }
});