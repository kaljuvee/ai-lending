import random
import os
from typing import Dict, List, Any
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LendingPromptGenerator:
    def __init__(self):
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE")
        )
        self.prompt_templates = {
            "personal_loans": {
                "name": "Personal Loans",
                "description": "Prompts for personal loan marketing campaigns",
                "templates": [
                    {
                        "title": "Competitive Rate Focus",
                        "template": "Create a {tone} {content_type} for personal loans targeting {audience} emphasizing our competitive interest rates starting at {rate}%. Highlight {benefit1} and {benefit2}. Include a call-to-action for {cta_action}.",
                        "variables": {
                            "tone": ["professional", "friendly", "urgent", "reassuring", "confident"],
                            "content_type": ["email campaign", "social media post", "blog article", "landing page", "advertisement"],
                            "audience": ["young professionals", "families", "first-time borrowers", "existing customers", "high-income earners"],
                            "rate": ["3.99", "4.25", "4.50", "4.75", "5.00"],
                            "benefit1": ["quick approval process", "flexible repayment terms", "no hidden fees", "online application", "same-day funding"],
                            "benefit2": ["excellent customer service", "transparent pricing", "flexible loan amounts", "early repayment options", "dedicated loan advisor"],
                            "cta_action": ["applying online today", "scheduling a consultation", "getting a free quote", "checking eligibility", "speaking with an advisor"]
                        }
                    },
                    {
                        "title": "Quick Approval Process",
                        "template": "Write a {content_type} promoting our {approval_time} personal loan approval process for {target_group}. Emphasize {key_feature} and mention that customers can {action_benefit}. Use a {tone} tone and include {social_proof}.",
                        "variables": {
                            "content_type": ["marketing email", "social media campaign", "website banner", "print advertisement", "video script"],
                            "approval_time": ["24-hour", "same-day", "instant", "48-hour", "express"],
                            "target_group": ["busy professionals", "small business owners", "students", "retirees", "millennials"],
                            "key_feature": ["digital-first application", "minimal documentation", "AI-powered underwriting", "streamlined process", "mobile-friendly platform"],
                            "action_benefit": ["get funds within 24 hours", "apply from their phone", "track application status online", "upload documents digitally", "receive instant pre-approval"],
                            "tone": ["exciting", "professional", "trustworthy", "modern", "customer-focused"],
                            "social_proof": ["customer testimonials", "industry awards", "satisfaction ratings", "success stories", "expert endorsements"]
                        }
                    }
                ]
            },
            "business_loans": {
                "name": "Business Loans",
                "description": "Prompts for business loan marketing campaigns",
                "templates": [
                    {
                        "title": "Growth-Focused Messaging",
                        "template": "Create a {content_format} for business loans targeting {business_type} looking to {growth_goal}. Highlight our {loan_feature} and {competitive_advantage}. Include information about {loan_amount} funding and {repayment_terms}.",
                        "variables": {
                            "content_format": ["comprehensive email series", "LinkedIn campaign", "industry publication ad", "webinar presentation", "case study"],
                            "business_type": ["startups", "established SMEs", "retail businesses", "manufacturing companies", "service providers"],
                            "growth_goal": ["expand operations", "purchase equipment", "hire new staff", "enter new markets", "increase inventory"],
                            "loan_feature": ["flexible terms", "competitive rates", "quick approval", "relationship banking", "industry expertise"],
                            "competitive_advantage": ["local market knowledge", "personalized service", "industry specialization", "technology platform", "partnership approach"],
                            "loan_amount": ["€10,000 to €500,000", "€25,000 to €1M", "€50,000 to €2M", "up to €5M", "customized amounts"],
                            "repayment_terms": ["flexible repayment schedules", "seasonal payment options", "interest-only periods", "early repayment benefits", "customized terms"]
                        }
                    },
                    {
                        "title": "Industry-Specific Solutions",
                        "template": "Develop a {marketing_piece} for {industry} businesses showcasing our specialized {loan_type} solutions. Focus on {industry_challenge} and how our {solution_approach} helps businesses {outcome}. Include {credibility_element}.",
                        "variables": {
                            "marketing_piece": ["industry report", "targeted email campaign", "trade show presentation", "partnership proposal", "thought leadership article"],
                            "industry": ["healthcare", "technology", "retail", "manufacturing", "hospitality"],
                            "loan_type": ["equipment financing", "working capital", "expansion loans", "acquisition financing", "bridge loans"],
                            "industry_challenge": ["seasonal cash flow", "equipment modernization", "regulatory compliance", "market expansion", "digital transformation"],
                            "solution_approach": ["industry expertise", "flexible structuring", "partnership model", "consultative approach", "technology integration"],
                            "outcome": ["achieve growth targets", "improve cash flow", "modernize operations", "expand market reach", "enhance competitiveness"],
                            "credibility_element": ["industry case studies", "sector expertise", "regulatory knowledge", "partnership testimonials", "market insights"]
                        }
                    }
                ]
            },
            "mortgage_loans": {
                "name": "Mortgage Loans",
                "description": "Prompts for mortgage and home loan marketing",
                "templates": [
                    {
                        "title": "First-Time Homebuyer Focus",
                        "template": "Create a {content_type} for first-time homebuyers highlighting our {mortgage_program} with {down_payment} down payment options. Emphasize {support_feature} and {educational_resource}. Use a {emotional_tone} tone that addresses {buyer_concern}.",
                        "variables": {
                            "content_type": ["educational email series", "homebuyer workshop", "social media campaign", "first-time buyer guide", "consultation offer"],
                            "mortgage_program": ["first-time buyer program", "government-backed loans", "low down payment options", "flexible qualification", "homebuyer assistance"],
                            "down_payment": ["3% minimum", "5% standard", "zero down", "flexible", "assisted"],
                            "support_feature": ["dedicated mortgage advisor", "step-by-step guidance", "online application", "pre-approval process", "closing support"],
                            "educational_resource": ["homebuying workshops", "online calculators", "buyer education materials", "market insights", "process guides"],
                            "emotional_tone": ["encouraging", "supportive", "informative", "reassuring", "empowering"],
                            "buyer_concern": ["affordability worries", "process complexity", "qualification uncertainty", "market timing", "documentation requirements"]
                        }
                    },
                    {
                        "title": "Refinancing Opportunities",
                        "template": "Write a {campaign_type} promoting mortgage refinancing for homeowners with {current_situation}. Highlight potential {savings_benefit} and our {refinance_feature}. Include {urgency_element} and {next_step}.",
                        "variables": {
                            "campaign_type": ["targeted email campaign", "direct mail piece", "digital advertisement", "rate alert notification", "consultation invitation"],
                            "current_situation": ["higher interest rates", "adjustable rate mortgages", "PMI payments", "cash-out needs", "term adjustments"],
                            "savings_benefit": ["monthly payment reduction", "interest savings", "cash-out options", "term flexibility", "PMI removal"],
                            "refinance_feature": ["streamlined process", "competitive rates", "no-cost options", "fast closing", "expert guidance"],
                            "urgency_element": ["current rate environment", "limited-time offers", "market conditions", "seasonal opportunities", "policy changes"],
                            "next_step": ["rate consultation", "savings analysis", "application start", "document preparation", "advisor meeting"]
                        }
                    }
                ]
            },
            "credit_cards": {
                "name": "Credit Cards",
                "description": "Prompts for credit card marketing campaigns",
                "templates": [
                    {
                        "title": "Rewards Program Focus",
                        "template": "Create a {marketing_format} for our {card_type} credit card featuring {rewards_structure}. Target {customer_segment} and highlight {key_benefit} and {additional_perk}. Include {promotional_offer} and use a {brand_voice} tone.",
                        "variables": {
                            "marketing_format": ["launch campaign", "social media series", "email promotion", "partnership marketing", "referral program"],
                            "card_type": ["cashback", "travel rewards", "business", "premium", "student"],
                            "rewards_structure": ["2% cashback on all purchases", "3x points on travel", "5% on rotating categories", "unlimited 1.5% cashback", "bonus point multipliers"],
                            "customer_segment": ["frequent travelers", "everyday spenders", "business owners", "young professionals", "premium customers"],
                            "key_benefit": ["no annual fee", "sign-up bonus", "flexible redemption", "travel benefits", "purchase protection"],
                            "additional_perk": ["mobile app features", "fraud protection", "customer service", "exclusive access", "financial tools"],
                            "promotional_offer": ["welcome bonus", "0% intro APR", "waived fees", "bonus categories", "limited-time rewards"],
                            "brand_voice": ["premium", "accessible", "innovative", "trustworthy", "customer-centric"]
                        }
                    }
                ]
            },
            "general_lending": {
                "name": "General Lending",
                "description": "Cross-product and general lending prompts",
                "templates": [
                    {
                        "title": "Trust and Credibility",
                        "template": "Develop a {content_piece} that establishes our credibility as a {institution_type} with {years_experience} years of experience. Highlight our {trust_factor} and {customer_commitment}. Include {social_proof} and position us as {market_position}.",
                        "variables": {
                            "content_piece": ["brand story", "about us page", "corporate brochure", "trust campaign", "reputation management"],
                            "institution_type": ["community bank", "digital lender", "credit union", "financial services company", "lending specialist"],
                            "years_experience": ["over 25", "more than 50", "nearly 100", "established since 1995", "decades of"],
                            "trust_factor": ["regulatory compliance", "transparent practices", "customer-first approach", "local community focus", "industry expertise"],
                            "customer_commitment": ["personalized service", "fair lending practices", "financial education", "long-term relationships", "responsible lending"],
                            "social_proof": ["customer testimonials", "industry awards", "regulatory ratings", "community involvement", "professional certifications"],
                            "market_position": ["trusted local partner", "innovative leader", "customer advocate", "community cornerstone", "financial ally"]
                        }
                    },
                    {
                        "title": "Digital Innovation",
                        "template": "Create a {digital_content} showcasing our {technology_feature} and how it {customer_benefit}. Target {tech_audience} and emphasize {innovation_aspect} while maintaining {security_message}. Include {user_experience} elements.",
                        "variables": {
                            "digital_content": ["app store description", "technology showcase", "digital banking campaign", "innovation announcement", "user guide"],
                            "technology_feature": ["mobile app", "online platform", "AI-powered tools", "digital onboarding", "automated processes"],
                            "customer_benefit": ["saves time", "improves convenience", "enhances security", "provides insights", "streamlines processes"],
                            "tech_audience": ["digital natives", "busy professionals", "tech-savvy customers", "mobile users", "online-first customers"],
                            "innovation_aspect": ["cutting-edge technology", "user-friendly design", "seamless integration", "advanced features", "continuous improvement"],
                            "security_message": ["bank-level security", "data protection", "fraud prevention", "secure transactions", "privacy protection"],
                            "user_experience": ["intuitive interface", "quick access", "personalized dashboard", "real-time updates", "24/7 availability"]
                        }
                    }
                ]
            }
        }
    
    def get_categories(self) -> List[Dict[str, str]]:
        """Get all available prompt categories"""
        return [
            {"key": key, "name": value["name"], "description": value["description"]}
            for key, value in self.prompt_templates.items()
        ]
    
    def get_templates_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all templates for a specific category"""
        if category in self.prompt_templates:
            return self.prompt_templates[category]["templates"]
        return []
    
    def generate_prompt(self, category: str, template_index: int, custom_variables: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate a prompt with random or custom variables"""
        if category not in self.prompt_templates:
            return {"error": "Category not found"}
        
        templates = self.prompt_templates[category]["templates"]
        if template_index >= len(templates):
            return {"error": "Template not found"}
        
        template_data = templates[template_index]
        template = template_data["template"]
        variables = template_data["variables"]
        
        # Use custom variables if provided, otherwise random selection
        selected_vars = {}
        for var_name, options in variables.items():
            if custom_variables and var_name in custom_variables:
                selected_vars[var_name] = custom_variables[var_name]
            else:
                selected_vars[var_name] = random.choice(options)
        
        # Generate the prompt
        try:
            generated_prompt = template.format(**selected_vars)
            return {
                "success": True,
                "prompt": generated_prompt,
                "variables_used": selected_vars,
                "template_title": template_data["title"],
                "category": self.prompt_templates[category]["name"]
            }
        except KeyError as e:
            return {"error": f"Missing variable: {e}"}
    
    def get_variable_options(self, category: str, template_index: int) -> Dict[str, List[str]]:
        """Get all variable options for a specific template"""
        if category not in self.prompt_templates:
            return {}
        
        templates = self.prompt_templates[category]["templates"]
        if template_index >= len(templates):
            return {}
        
        return templates[template_index]["variables"]
    
    def create_custom_prompt(self, base_template: str, variables: Dict[str, str]) -> Dict[str, Any]:
        """Create a custom prompt from a base template and variables"""
        try:
            generated_prompt = base_template.format(**variables)
            return {
                "success": True,
                "prompt": generated_prompt,
                "variables_used": variables
            }
        except KeyError as e:
            return {"error": f"Missing variable: {e}"}
    
    def get_prompt_suggestions(self, loan_type: str, audience: str, goal: str) -> List[str]:
        """Get prompt suggestions based on loan type, audience, and goal"""
        suggestions = []
        
        # Base suggestions
        base_prompts = [
            f"Create a compelling {loan_type} campaign for {audience} focusing on {goal}",
            f"Write a persuasive email series about {loan_type} targeting {audience} to achieve {goal}",
            f"Develop social media content for {loan_type} that resonates with {audience} and drives {goal}",
            f"Design a landing page for {loan_type} that converts {audience} visitors into {goal}",
            f"Create educational content about {loan_type} that helps {audience} understand {goal}"
        ]
        
        # Add specific suggestions based on loan type
        if "personal" in loan_type.lower():
            suggestions.extend([
                f"Highlight competitive rates and quick approval for {audience}",
                f"Emphasize flexible terms and transparent pricing for {audience}",
                f"Focus on life events and financial goals for {audience}"
            ])
        elif "business" in loan_type.lower():
            suggestions.extend([
                f"Showcase growth opportunities and expansion funding for {audience}",
                f"Highlight industry expertise and partnership approach for {audience}",
                f"Emphasize cash flow solutions and equipment financing for {audience}"
            ])
        elif "mortgage" in loan_type.lower():
            suggestions.extend([
                f"Focus on homeownership dreams and first-time buyer programs for {audience}",
                f"Highlight refinancing opportunities and rate savings for {audience}",
                f"Emphasize local market knowledge and homebuyer education for {audience}"
            ])
        
        return base_prompts + suggestions[:3]  # Return base + 3 specific suggestions
    
    def generate_content_with_openai(self, prompt: str, content_type: str = "marketing copy") -> Dict[str, Any]:
        """Generate actual marketing content using OpenAI based on the prompt"""
        try:
            system_prompt = f"""You are an expert marketing copywriter specializing in financial services and lending products. 
            Create compelling, compliant, and effective {content_type} that:
            - Follows financial advertising regulations
            - Uses persuasive but honest language
            - Includes clear calls-to-action
            - Is appropriate for European markets
            - Maintains professional tone while being engaging
            - Includes relevant disclaimers when needed
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "content": content,
                "prompt_used": prompt,
                "content_type": content_type,
                "tokens_used": response.usage.total_tokens if response.usage else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prompt_used": prompt
            }
    
    def enhance_prompt_with_ai(self, basic_prompt: str, enhancement_type: str = "detailed") -> Dict[str, Any]:
        """Use AI to enhance and improve a basic prompt"""
        try:
            enhancement_prompts = {
                "detailed": "Take this basic marketing prompt and make it more detailed, specific, and actionable. Add relevant context, target audience insights, and specific requirements:",
                "creative": "Transform this basic marketing prompt into a more creative and engaging version. Add emotional hooks, storytelling elements, and unique angles:",
                "compliance": "Enhance this marketing prompt to ensure it includes all necessary compliance considerations for financial services marketing in Europe:",
                "conversion": "Optimize this marketing prompt to focus on conversion and performance. Add elements that drive action and measurable results:"
            }
            
            system_prompt = f"""You are a marketing prompt optimization expert. {enhancement_prompts.get(enhancement_type, enhancement_prompts['detailed'])}
            
            Return an enhanced version that is more specific, actionable, and effective for creating high-quality marketing content."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": basic_prompt}
                ],
                max_tokens=500,
                temperature=0.6
            )
            
            enhanced_prompt = response.choices[0].message.content
            
            return {
                "success": True,
                "enhanced_prompt": enhanced_prompt,
                "original_prompt": basic_prompt,
                "enhancement_type": enhancement_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_prompt": basic_prompt
            }
    
    def generate_prompt_variations(self, base_prompt: str, num_variations: int = 3) -> Dict[str, Any]:
        """Generate multiple variations of a prompt using AI"""
        try:
            system_prompt = f"""Create {num_variations} different variations of the following marketing prompt. 
            Each variation should:
            - Maintain the core intent and goals
            - Use different approaches, angles, or emphasis
            - Be suitable for different audiences or contexts
            - Remain focused on lending/financial services
            
            Return the variations as a numbered list."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Base prompt: {base_prompt}"}
                ],
                max_tokens=800,
                temperature=0.8
            )
            
            variations_text = response.choices[0].message.content
            
            # Parse variations (simple parsing, could be improved)
            variations = []
            lines = variations_text.split('\n')
            current_variation = ""
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    if current_variation:
                        variations.append(current_variation.strip())
                    current_variation = line
                elif line and current_variation:
                    current_variation += " " + line
            
            if current_variation:
                variations.append(current_variation.strip())
            
            return {
                "success": True,
                "variations": variations,
                "base_prompt": base_prompt,
                "count": len(variations)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "base_prompt": base_prompt
            }

