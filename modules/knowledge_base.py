# Full Content Replication from data/knowledgeBase.ts

DEFAULT_KNOWLEDGE_BASE = [
  {
    "id": "week_1",
    "week": 1,
    "title": "Thermodynamics & IC Engine Basics",
    "difficulty": "Beginner",
    "summary": "Introduction to the four laws of thermodynamics, Otto vs Diesel cycles, and internal combustion engine principles.",
    "theory": """
    **The Four Laws of Thermodynamics**
    1. **Zeroth Law**: Defines thermal equilibrium.
    2. **First Law**: Energy cannot be created or destroyed (Conservation of Energy).
    3. **Second Law**: Entropy of an isolated system always increases. Heat flows from hot to cold.
    4. **Third Law**: Entropy approaches a constant value as temperature approaches absolute zero.

    **Otto vs Diesel Cycles**
    - **Otto Cycle (Petrol)**: Intake -> Compression -> Combustion (Spark) -> Expansion -> Exhaust.
    - **Diesel Cycle**: Intake -> Compression -> Combustion (Compression Ignition) -> Expansion -> Exhaust.
    
    *Key Difference*: Petrol engines use spark plugs; Diesel engines use high compression to self-ignite fuel.
    """,
    "objectives": ["Understand 4 laws of thermodynamics", "Describe Otto/Diesel cycles", "Differentiate Petrol vs Diesel"]
  },
  {
    "id": "week_2",
    "week": 2, 
    "title": "Mechanical Elements",
    "difficulty": "Beginner", 
    "summary": "Focuses on shafts, axles, bearings, and gear trains (Spur, Helical, Bevel) for power transmission.",
    "theory": """
    **Shafts & Axles**
    - **Shaft**: Rotating element that transmits power (e.g., drive shaft).
    - **Axle**: Stationary or rotating element that supports wheels/weight.

    **Gears**
    - **Spur Gears**: Straight teeth, noisy, good for low speed.
    - **Helical Gears**: Angled teeth, smoother, higher load capacity.
    - **Bevel Gears**: Transmit power at 90-degree angles.
    
    **Gear Ratio**: Ratio of teeth on Driven Gear / Driver Gear. Determines torque vs speed trade-off.
    """,
    "objectives": ["Functions of shafts/axles", "Identify gear types", "Calculate gear ratios"]
  },
  {
    "id": "week_17",
    "week": 17,
    "title": "EV Introduction & Architecture",
    "difficulty": "Intermediate",
    "summary": "Foundational understanding of Electric Vehicles, powertrain architecture (Battery, Inverter, Motor), and types (BEV, PHEV, FCEV).",
    "theory": """
    **EV Powertrain Architecture**
    1. **Battery Pack**: Stores DC energy (Lithium-ion).
    2. **Inverter**: Converts DC to AC for the motor.
    3. **Electric Motor**: Propels the vehicle.
    4. **OBC (On-Board Charger)**: Converts Grid AC to DC for charging.

    **Types of EVs**
    - **BEV**: Battery Electric (Pure electric).
    - **HEV**: Hybrid (Gas + Electric, no plug).
    - **PHEV**: Plug-in Hybrid (Gas + Electric + Plug).
    - **FCEV**: Hydrogen Fuel Cell.
    """,
    "objectives": ["Describe EV powertrain", "Differentiate BEV/PHEV/FCEV", "Understand market trends"]
  },
  {
    "id": "week_21",
    "week": 21,
    "title": "Introduction to AI Tools",
    "difficulty": "Advanced",
    "summary": "Overview of LLMs (ChatGPT, Gemini), multimodal AI, and ethical considerations in engineering applications.",
    "theory": """
    **Key AI Tools**
    - **ChatGPT (OpenAI)**: Conversational reasoning & code generation.
    - **Gemini (Google)**: Multimodal (Text, Image, Video) native processing.
    - **Perplexity**: Real-time cited research.

    **Engineering Applications**
    - Automating SOP generation.
    - Predictive maintenance algorithms.
    - Generative design for CAD.

    **Ethics**: Beware of 'Hallucinations' (confident but false info) and Data Privacy when using proprietary blueprints.
    """,
    "objectives": ["Identify AI tools", "Describe engineering applications", "Understand AI ethics"]
  }
]