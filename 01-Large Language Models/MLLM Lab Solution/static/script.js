let currentIndex = 0;

document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Initialize references to DOM elements
        var prevButton = document.getElementById("prev-button");
        var nextButton = document.getElementById("next-button");
        var overlay = document.getElementById("overlay");
        var viewer = document.getElementById("viewer");
        var slide = document.getElementById("slide");
        var audio = document.getElementById("audio");

        // Get the slide count and initialize the UI
        var slideCount = await getSlideCount();
        prevButton.disabled = (currentIndex == 0);
        nextButton.disabled = (currentIndex == slideCount - 1);

        if (slideCount > 0) {
            // Load the first slide
            await loadContent(currentIndex, slide, audio, overlay);
            viewer.style.display = "block";
        }

        // Process clicks of the Previous button
        prevButton.addEventListener("click", async (e) => {
            if (currentIndex > 0) {
                currentIndex -= 1;
                prevButton.disabled = (currentIndex == 0);
                nextButton.disabled = (currentIndex == slideCount - 1);
                await loadContent(currentIndex, slide, audio, overlay);
            }
        });

        // Process clicks of the Next button
        nextButton.addEventListener("click", async (e) => {
            if (currentIndex < slideCount - 1) {
                currentIndex += 1;
                prevButton.disabled = (currentIndex == 0);
                nextButton.disabled = (currentIndex == slideCount - 1);
                await loadContent(currentIndex, slide, audio, overlay);
            }
        });
    }
    catch(error) {
        overlay.style.display = "none";
        alert(`${error}`);
    }
});

async function getSlideCount() {
    var response = await fetch('/get_slide_count');
    var data = await response.json();
    return data.count;
}

async function getSlide(index) {
    var response = await fetch(`/get_slide/${index}`);
    var data = await response.json();
    return data;
}

async function getAudio(index) {
    var response = await fetch(`/get_audio/${index}`);
    var data = await response.json();
    return data.audio_url;
}

async function loadContent(index, slide, audio, overlay) {
    audio.pause();
    audio.currentTime = 0;
    audio.src = "";

    // Load the slide image
    var data = await getSlide(index);
    slide.src = data.image_url;

    if (data.audio_url.length > 0) {
        // If audio is available, use it
        audio.src = data.audio_url;
    }
    else {
        // Otherwise generate audio for the slide
        overlay.style.display = "block";
        audio_url = await getAudio(index);
        audio.src = audio_url;
        overlay.style.display = "none";
    }
}
