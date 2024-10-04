$(function() {
    $("#answer-button").click(async e => {
        e.preventDefault(); // Prevent postback

        // Get the question from the input field
        var question = $("#question")
        var query = question.val().trim();

        if (query.length > 0) {
            // Clear the output
            var answer = $("#answer");
            answer.text("");
            
            // Submit the question
            var response = await fetch('/answer?query=' + query);

            // Show the response
            answer.append((await response.text()).replaceAll("\n", "<br />"));
        }
    });
});