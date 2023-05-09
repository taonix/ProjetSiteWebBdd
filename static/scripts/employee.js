let button = document.getElementById('questionnaireRempli');

button.onclick = function() {
    window.location.href = '/questionnairesRemplis';
};

function remplir(questionnaireId) {
    window.location.href = '/remplir/'+questionnaireId;
}