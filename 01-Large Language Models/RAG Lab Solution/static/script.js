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
            var reader = response.body.getReader();
            var decoder = new TextDecoder("utf-8");

            // Display the streaming response
            while (true) {
                var { done, value } = await reader.read();
                if (done) break;
                var chunk = decoder.decode(value, { stream: true });
                answer.append(chunk.replaceAll("\n", "<br />"));
            }
        }
    });
});