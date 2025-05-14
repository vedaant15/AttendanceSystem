document.addEventListener("DOMContentLoaded", function () {
   fetch('data/attendance.csv')

        .then(response => response.text())
        .then(data => {
            const rows = data.trim().split("\n");
            const tbody = document.querySelector("#attendance-table tbody");

            rows.forEach(row => {
                const [name, timestamp] = row.split(",");
                const tr = document.createElement("tr");
                tr.innerHTML = `<td>${name}</td><td>${timestamp}</td>`;
                tbody.appendChild(tr);
            });
        })
        .catch(error => {
            console.error("Error loading CSV:", error);
            alert("Could not load attendance file.");
        });
});
