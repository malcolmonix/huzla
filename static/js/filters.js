document.addEventListener('DOMContentLoaded', function() {
    const regionFilter = document.getElementById('regionFilter');
    const stateFilter = document.getElementById('stateFilter');
    
    function updateStateOptions() {
        const selectedRegion = regionFilter.value;
        const stateOptions = stateFilter.querySelectorAll('option');
        
        stateOptions.forEach(option => {
            if (!selectedRegion || option.value === '' || 
                option.dataset.region === selectedRegion) {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    regionFilter.addEventListener('change', function() {
        updateStateOptions();
        stateFilter.value = '';
        document.getElementById('searchForm').submit();
    });
    
    stateFilter.addEventListener('change', function() {
        document.getElementById('searchForm').submit();
    });
    
    updateStateOptions();
}); 