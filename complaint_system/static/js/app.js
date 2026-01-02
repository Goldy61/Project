// ---------------- USER: AJAX COMPLAINT SUBMIT ----------------
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("complaintForm");

    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault(); // 🚨 REQUIRED

            fetch("/submit_complaint", {
                method: "POST",
                body: new FormData(form)
            })
            .then(res => res.json())
            .then(() => {
                document.getElementById("msg").innerHTML =
                    "<div class='alert alert-success'>Complaint submitted successfully</div>";
                form.reset();
            });
        });
    }



    // ---------------- ADMIN: CHART ----------------
    const chartCanvas = document.getElementById("complaintChart");
    if (chartCanvas) {
        fetch("/admin_chart_data")
            .then(res => res.json())
            .then(data => {
                new Chart(chartCanvas, {
                    type: "bar",
                    data: {
                        labels: ["Pending", "In Progress", "Resolved"],
                        datasets: [{
                            label: "Complaints",
                            data: [
                                data["Pending"],
                                data["In Progress"],
                                data["Resolved"]
                            ],
                            backgroundColor: ["orange", "blue", "green"]
                        }]
                    }
                });
            });
    }
});
