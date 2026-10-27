import re
import math

class MathHandler:
    """Detect and solve math problems locally before hitting the web"""
    
    FORMULAS = {
        "(a+b)^2": "**Formula:** (a + b)² = a² + 2ab + b²\n\n**Example:** (3+4)² = 3² + 2(3)(4) + 4² = 9 + 24 + 16 = 49",
        "(a+b)2": "**Formula:** (a + b)² = a² + 2ab + b²\n\n**Example:** (3+4)² = 9 + 24 + 16 = 49",
        "(a-b)^2": "**Formula:** (a − b)² = a² − 2ab + b²\n\n**Example:** (5−2)² = 25 − 20 + 4 = 9",
        "(a-b)2": "**Formula:** (a − b)² = a² − 2ab + b²",
        "a^2-b^2": "**Formula:** a² − b² = (a + b)(a − b)\n\n**Example:** 9² − 4² = (9+4)(9−4) = 13 × 5 = 65",
        "a^2+b^2": "**Formula:** a² + b² = (a + b)² − 2ab",
        "(a+b)^3": "**Formula:** (a + b)³ = a³ + 3a²b + 3ab² + b³",
        "(a-b)^3": "**Formula:** (a − b)³ = a³ − 3a²b + 3ab² − b³",
        "quadratic formula": "**Formula:** x = (−b ± √(b² − 4ac)) / (2a)\n\nFor: ax² + bx + c = 0\n\n**Discriminant:** D = b² − 4ac\n• D > 0 → 2 real roots\n• D = 0 → 1 real root\n• D < 0 → 2 complex roots",
        "area of circle": "**Formula:** Area = π × r²\n\n**Example:** r = 5 → Area = π × 25 ≈ 78.54",
        "circumference of circle": "**Formula:** C = 2 × π × r\n\n**Example:** r = 5 → C ≈ 31.42",
        "area of triangle": "**Formula:** Area = ½ × base × height",
        "area of rectangle": "**Formula:** Area = length × width",
        "area of square": "**Formula:** Area = side²",
        "pythagoras theorem": "**Formula:** a² + b² = c²\n\nWhere c is the hypotenuse (longest side) of a right triangle.",
        "pythagorean theorem": "**Formula:** a² + b² = c²",
        "volume of sphere": "**Formula:** V = (4/3) × π × r³",
        "volume of cube": "**Formula:** V = side³",
        "volume of cylinder": "**Formula:** V = π × r² × h",
        "sin formula": "**Formula:** sin(θ) = Opposite / Hypotenuse",
        "cos formula": "**Formula:** cos(θ) = Adjacent / Hypotenuse",
        "tan formula": "**Formula:** tan(θ) = Opposite / Adjacent",
        "sin^2+cos^2": "**Identity:** sin²θ + cos²θ = 1",
        "einstein equation": "**Formula:** E = mc²\n\nE = energy, m = mass, c = speed of light",
        "newton second law": "**Formula:** F = m × a",
        "kinetic energy": "**Formula:** KE = ½ × m × v²",
        "potential energy": "**Formula:** PE = m × g × h",
        "speed formula": "**Formula:** Speed = Distance / Time",
    }
    
    SAFE_FUNCTIONS = {
        "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "log": math.log, "log10": math.log10, "exp": math.exp, "abs": abs,
        "pi": math.pi, "e": math.e, "pow": pow, "round": round,
    }
    
    def solve(self, query: str):
        formula_result = self._check_formula(query)
        if formula_result:
            return formula_result
        
        math_result = self._evaluate_expression(query)
        if math_result:
            return math_result
        
        return None
    
    def _check_formula(self, query: str):
        q = query.lower().strip()
        q = q.replace(" ", "").replace("formula", "").replace("?", "").replace("=", "")
        
        for formula_key, formula_text in self.FORMULAS.items():
            key_normalized = formula_key.replace(" ", "")
            if key_normalized in q or q in key_normalized:
                return {"source": "Math Formula", "answer": formula_text, "url": ""}
        
        return None
    
    def _evaluate_expression(self, query: str):
        q = query.strip().rstrip("=? ").strip()
        q = q.replace("plus", "+").replace("minus", "-")
        q = q.replace("times", "*").replace("multiplied by", "*")
        q = q.replace("divided by", "/").replace("÷", "/")
        q = q.replace("^", "**").replace("×", "*").replace(",", "")
        
        # Must have digit AND operator
        if not re.search(r'\d', q):
            return None
        if not re.search(r'[\+\-\*/]', q):
            return None
        
        # Must be only math characters
        cleaned = q.lower()
        for func in self.SAFE_FUNCTIONS:
            cleaned = cleaned.replace(func, "")
        cleaned = cleaned.replace("math.", "")
        
        if not re.match(r'^[\d\s\+\-\*/\(\)\.\^%]+$', cleaned):
            return None
        
        try:
            code = compile(q, "<math>", "eval")
            for name in code.co_names:
                if name not in self.SAFE_FUNCTIONS:
                    return None
            
            result = eval(code, {"__builtins__": {}}, self.SAFE_FUNCTIONS)
            
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 6)
            
            display = query.strip().rstrip("=? ").strip()
            return {
                "source": "Math",
                "answer": f"**{display} = {result}**",
                "url": ""
            }
        except Exception:
            return None