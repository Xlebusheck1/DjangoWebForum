function getCookie(name) {
    const value = document.cookie
        .split('; ')
        .find(row => row.startsWith(name + '='));
    return value ? decodeURIComponent(value.split('=')[1]) : null;
}

function sendLike(question_id) {
    const ratingElement = document.getElementById(
        `question-${question_id}-rating`
    );

    fetch(`/api/question/${question_id}/like/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams({
            pk: question_id,
            is_like: 'true',
        }),
    })
    .then(res => res.json())
    .then(data => {
        if (data.success && data.rating !== undefined && ratingElement) {
            ratingElement.textContent = data.rating;
        }
    })
    .catch(err => console.error('like error:', err));
}