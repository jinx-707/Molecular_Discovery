import pytest
from backend.app.simulation.energy import ReactionEnergyEstimator
from backend.app.simulation.flux import MetabolicFluxAnalyzer
from backend.app.simulation.validator import StructureValidator

def test_energy_profile():
    est = ReactionEnergyEstimator()
    profile = est.get_energy_profile("CO2 + H2", "TiO2")
    assert "transition_state_energy" in profile
    assert profile["transition_state_energy"] > 0
    assert isinstance(profile["intermediates"], dict)

def test_flux():
    analyzer = MetabolicFluxAnalyzer()
    flux = analyzer.predict_flux(["b00999", "b01105"])
    assert "yield" in flux
    assert 0 < flux["yield"] <= 1

def test_validator():
    val = StructureValidator()
    cat_valid = val.validate_catalyst("TiO2 crystal")
    assert "valid" in cat_valid
    enz_valid = val.validate_enzyme("MAKVPLAG...")
    assert "ss_content" in enz_valid

if __name__ == "__main__":
    pytest.main(["-v"])

