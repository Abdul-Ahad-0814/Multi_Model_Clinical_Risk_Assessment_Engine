function showStage2(selectedDiseases) {
    // hide all stage2 sections
    document.querySelectorAll('.stage2').forEach(sec => sec.style.display = 'none');

    // show selected disease stage2
    selectedDiseases.forEach(disease => {
        let sec = document.getElementById(disease + '_stage2');
        if(sec) sec.style.display = 'block';
    });
}
