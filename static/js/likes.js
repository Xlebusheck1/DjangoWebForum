function getCookie(name) {
    const value = document.cookie
        .split("; ")
        .find((row) => row.startsWith(name + "="));
    return value ? decodeURIComponent(value.split("=")[1]) : null;
}

function toggleLike(question_id) {
    const ratingElement = document.getElementById(`question-${question_id}-rating`);
    if (!ratingElement) return;

    const btn = document.querySelector(`button.like-question-btn[data-question-id="${question_id}"]`);
    if (!btn) return;

    const icon = btn.querySelector("i");
    if (!icon) return;

    const currentlyLiked = btn.dataset.liked === "true";
    const nextIsLike = !currentlyLiked;

    fetch(`/api/question/${question_id}/like/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            is_like: String(nextIsLike),
        }),
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then((data) => {
        if (data.success && data.rating !== undefined) {
            ratingElement.textContent = data.rating;
            btn.dataset.liked = String(nextIsLike);

            if (nextIsLike) {
                btn.classList.add("like-btn--active");
                btn.classList.remove("like-btn--inactive");
                icon.classList.remove("far");
                icon.classList.add("fas");
            } else {
                btn.classList.add("like-btn--inactive");
                btn.classList.remove("like-btn--active");
                icon.classList.remove("fas");
                icon.classList.add("far");
            }
        } else if (data.error) {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch((err) => {
        console.error("like toggle error:", err);
        alert('Произошла ошибка при установке лайка');
    });
}

function toggleAnswerLike(answer_id) {
    const ratingElement = document.getElementById(`answer-${answer_id}-rating`);
    if (!ratingElement) return;

    const btn = document.querySelector(`button.like-answer-btn[data-answer-id="${answer_id}"]`);
    if (!btn) return;

    const icon = btn.querySelector("i");
    if (!icon) return;

    const currentlyLiked = btn.dataset.liked === "true";
    const nextIsLike = !currentlyLiked;

    fetch(`/api/answer/${answer_id}/like/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            is_like: String(nextIsLike),
        }),
    })
    .then((response) => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then((data) => {
        if (data.success && data.rating !== undefined) {
            ratingElement.textContent = data.rating;
            btn.dataset.liked = String(nextIsLike);

            if (nextIsLike) {
                btn.classList.add("like-btn--active");
                btn.classList.remove("like-btn--inactive");
                icon.classList.remove("far");
                icon.classList.add("fas");
            } else {
                btn.classList.add("like-btn--inactive");
                btn.classList.remove("like-btn--active");
                icon.classList.remove("fas");
                icon.classList.add("far");
            }
        } else if (data.error) {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch((err) => {
        console.error("answer like toggle error:", err);
        alert('Произошла ошибка при установке лайка');
    });
}

function markCorrectAnswer(answer_id) {
    fetch("/api/answer/mark-correct/", {
        method: "POST",
        headers: {
            "X-CSRFToken": getCookie("csrftoken"),
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: new URLSearchParams({
            pk: answer_id,
        }),
    })
    .then((response) => response.json())
    .then((data) => {
        if (data.success) {
            location.reload();
        }
    })
    .catch((err) => console.error("mark correct error:", err));
}

document.addEventListener("DOMContentLoaded", () => {    
    document.querySelectorAll(".like-answer-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const answerId = btn.dataset.answerId;
            toggleAnswerLike(answerId);
        });
    });
    
    document.querySelectorAll(".like-question-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const qId = btn.dataset.questionId;
            toggleLike(qId);
        });
    });
    
    document.querySelectorAll(".answer-mark-correct-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            const answerId = btn.dataset.answerId;
            markCorrectAnswer(answerId);
        });
    });
});