from auraseal512 import generate_auraseal514_components

journey = """
NOV 8, 2025
15 EVESHAM WAY IG5 0EQ → JUBILEE CHURCH IG1 4JY
2.8km walk / Bus 128 | 33 mins / 20 mins
Referral: SECURED | Healthcare Service Start
3-Day Seal: ACTIVE | Obi Nami En Route
"""
seal = ''.join(generate_auraseal514_components(journey))
print("JOURNEY AURASEAL:", seal[:64] + "...")  # Your 514-hex armor
