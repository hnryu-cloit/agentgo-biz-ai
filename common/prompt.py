class RENDERING:
    """
    렌더링 이미지 생성용 프롬프트
    """

    @staticmethod
    def rendering_prompt(product_name, target_angle: str, angle_descriptions: list, base_style=None) -> str:
        columns_info = ", ".join([f"Column {i + 1}: {angle}" for i, angle in enumerate(angle_descriptions)])

        return f"""
        Task: Generate a highly realistic e-commerce product photograph of the {product_name}.

        --- CRITICAL 3D GEOMETRY & ROTATION ANALYSIS ---
        I have provided a SINGLE reference image containing a 3-TIER Multi-View Blueprint Grid.
        - GRID LAYOUT: {columns_info}.
        - TOP ROW (Row 1): Reference images for EXACT colors, textures, and materials.
        - MIDDLE & BOTTOM ROWS (Depth & Edge Maps): These represent the ABSOLUTE 3D GEOMETRY of the furniture.

        RULE 1 (ISOLATE MAIN SUBJECT - NO PROPS): Identify the primary furniture item ({product_name}). You MUST completely IGNORE and REMOVE any unattached staging items, lifestyle props, or loose accessories (such as decorative objects, loose fabrics, pillows, or unattached elements resting on the furniture). Render ONLY the bare main furniture.
        RULE 2 (STRICT 3D GEOMETRY PRESERVATION - NO ADDITIONS): You MUST treat the Edge and Depth maps as the absolute exact boundary of the physical shape. DO NOT add, invent, or hallucinate any new structural components. If the maps show a simple straight sofa, DO NOT add a chaise lounge, ottoman, extended seating, or extra armrests. The generated shape must 100% match the structural volume defined in the blueprints, nothing more, nothing less.
        RULE 3 (MENTAL 3D ROTATION TO TARGET ANGLE): The final render MUST be exactly a '{target_angle}'. You MUST mentally rotate the exact 3D object defined in the blueprint to match this new angle. 
        RULE 4 (PERFECT STRUCTURAL INTEGRITY): While the 2D outline will naturally change because you are rotating the object, the underlying 3D structure of the bare furniture MUST remain rigidly locked. Do not extend the length or width beyond what is given.
        RULE 5 (EXACT COLOR MATCHING - CRITICAL): You MUST extract the EXACT color, shade, and fabric texture from the original reference images in the TOP ROW. DO NOT change, neutralize, or alter the color to match the '{base_style}' style.
        RULE 6 (OUTPUT FORMAT & SEAMLESS ENVIRONMENT): Render ONLY the final lifelike product. If the output aspect ratio leaves empty space, completely fill it by naturally extending a premium studio backdrop or highly realistic environment. DO NOT generate black bars, letterboxes, or random sketches in the negative space. Do not replicate the blueprint layout.
        RULE 7 (STRICT FRAMING): Frame the furniture beautifully in the center. The background must be perfectly clean and seamless from edge to edge.

        Final Render Angle: {target_angle}, perfectly centered.
        Background: Seamless premium studio backdrop extending smoothly to all edges.
        Quality: 8k resolution, photorealistic, exact original color preservation, sharp focus, strictly no props, NO extra structures added, seamlessly integrated background, NO black borders.
        """
