<script>
    document.getelementById('resumeForm').addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new formData(this);

        const response = await fetch('/analyze', {
         method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        document.getelementById('results').classList.remove('d-none');
        document.getelementById('score').innerText = data.score;
        document.getelementById('match').innerText = data.match;

        const suggestionsList = document.getelementById('suggestions');
        suggestions
    })
</script>