import spacy
from typing import Dict, Any, List
from decimal import Decimal
from .base import BaseGradingService

class SpacyGradingService(BaseGradingService):
    '''
    NLP-based grading service using spaCy for semantic similarity.
    Provides fair grading by understanding meaning, not just exact matches.
    '''

    def __init__(self):
        try:
            self.nlp = spacy.load('en_core_web_md')
        except OSError:
            raise Exception(
                "spaCy model not found. Please run: "
                "python -m spacy download en_core_web_md"
            )

        # Grading weights
        self.keyword_weight = 0.4  # 40% for keyword similarity
        self.content_weight = 0.4  # 40% for overall content similarity
        self.completeness_weight = 0.2  # 20% for answer completeness

        # Thresholds
        self.similarity_threshold = 0.6  # Minimum similarity to consider a match

    def grade_submission(self, submission) -> Dict[str, Any]:
        '''Grade all answers in a submission.'''

        total_obtained = Decimal('0.00')
        answer_results = []

        for answer in submission.answers.all():
            result = self.grade_answer(answer, answer.question)

            answer.marks_obtained = Decimal(str(result['marks_obtained']))
            answer.feedback = result['feedback']
            answer.save()

            total_obtained += answer.marks_obtained
            answer_results.append(result)

        # Update submission
        submission.obtained_marks = total_obtained
        submission.percentage = submission.calculate_percentage()
        submission.save()

        return {
            'total_obtained': float(total_obtained),
            'total_marks': float(submission.total_marks),
            'percentage': float(submission.percentage),
            'answer_results': answer_results
        }

    def grade_answer(self, answer, question) -> Dict[str, Any]:
        '''Grade an individual answer using NLP semantic similarity.'''

        # Process texts with spaCy
        user_answer_doc = self.nlp(answer.answer_text.lower().strip())
        expected_answer_doc = self.nlp(question.expected_answer.lower().strip())

        # Get keywords (or extract from expected answer)
        keywords = question.keywords if question.keywords else []
        if not keywords:
            keywords = self._extract_keywords_nlp(expected_answer_doc)

        # Calculate three components of grading
        keyword_score = self._calculate_keyword_similarity(user_answer_doc, keywords)
        content_score = self._calculate_content_similarity(user_answer_doc, expected_answer_doc)
        completeness_score = self._calculate_completeness(user_answer_doc, expected_answer_doc)

        # Calculate weighted total score
        total_score = (
                keyword_score * self.keyword_weight +
                content_score * self.content_weight +
                completeness_score * self.completeness_weight
        )

        # Calculate marks
        marks_obtained = total_score * float(question.marks)

        # Generate detailed feedback
        feedback = self._generate_feedback(
            keyword_score,
            content_score,
            completeness_score,
            keywords,
            user_answer_doc
        )

        return {
            'marks_obtained': round(marks_obtained, 2),
            'marks_allocated': float(question.marks),
            'keyword_similarity': round(keyword_score * 100, 2),
            'content_similarity': round(content_score * 100, 2),
            'completeness_score': round(completeness_score * 100, 2),
            'total_score': round(total_score * 100, 2),
            'feedback': feedback
        }

    def _extract_keywords_nlp(self, doc, max_keywords: int = 8) -> List[str]:
        '''Extract important keywords using NLP (nouns, proper nouns, key verbs).'''

        keywords = []

        # Extract named entities
        for ent in doc.ents:
            keywords.append(ent.text.lower())

        # Extract important nouns and verbs
        for token in doc:
            # Focus on nouns, proper nouns, and important verbs
            if token.pos_ in ['NOUN', 'PROPN', 'VERB'] and not token.is_stop:
                # Only add if significant length
                if len(token.text) > 2:
                    keywords.append(token.lemma_.lower())

        # Remove duplicates and limit
        keywords = list(dict.fromkeys(keywords))[:max_keywords]
        return keywords

    def _calculate_keyword_similarity(self, user_doc, keywords: List[str]) -> float:
        '''Calculate how well user answer covers keywords using semantic similarity.'''

        if not keywords:
            return 0.7  # Neutral score if no keywords

        total_similarity = 0.0
        matched_keywords = 0

        for keyword in keywords:
            keyword_doc = self.nlp(keyword)

            # Calculate similarity between keyword and user answer
            similarity = user_doc.similarity(keyword_doc)

            # If similarity is above threshold, consider it a match
            if similarity >= self.similarity_threshold:
                matched_keywords += 1
                total_similarity += similarity
            else:
                # Check if keyword appears in any form in the answer
                keyword_lemma = keyword_doc[0].lemma_ if len(keyword_doc) > 0 else keyword
                for token in user_doc:
                    if token.lemma_ == keyword_lemma or keyword in token.text:
                        matched_keywords += 1
                        total_similarity += 0.8
                        break

        # Calculate score: average of match rate and average similarity
        match_rate = matched_keywords / len(keywords)
        avg_similarity = (total_similarity / len(keywords)) if matched_keywords > 0 else 0

        return (match_rate + avg_similarity) / 2

    def _calculate_content_similarity(self, user_doc, expected_doc) -> float:
        '''Calculate overall semantic similarity between user and expected answer.'''

        # Use spaCy's built-in similarity (cosine similarity of word vectors)
        similarity = user_doc.similarity(expected_doc)

        # Normalize score (spaCy similarity can be negative)
        normalized_score = max(0, min(1, similarity))

        return normalized_score

    def _calculate_completeness(self, user_doc, expected_doc) -> float:
        '''Calculate answer completeness based on key concepts coverage.'''

        # Extract key concepts from expected answer
        expected_concepts = set()
        for chunk in expected_doc.noun_chunks:
            expected_concepts.add(chunk.root.lemma_)

        # Extract concepts from user answer
        user_concepts = set()
        for chunk in user_doc.noun_chunks:
            user_concepts.add(chunk.root.lemma_)

        if not expected_concepts:
            return 0.7  # Neutral score

        # Calculate how many expected concepts are covered
        covered_concepts = 0
        for exp_concept in expected_concepts:
            exp_doc = self.nlp(exp_concept)
            for user_concept in user_concepts:
                user_concept_doc = self.nlp(user_concept)
                if exp_doc.similarity(user_concept_doc) >= self.similarity_threshold:
                    covered_concepts += 1
                    break

        coverage = covered_concepts / len(expected_concepts)

        # Also consider answer length (not too short, not excessively long)
        length_ratio = len(user_doc) / max(len(expected_doc), 1)
        length_score = 1.0 if 0.5 <= length_ratio <= 2.0 else 0.7

        return (coverage + length_score) / 2

    def _generate_feedback(
            self,
            keyword_score: float,
            content_score: float,
            completeness_score: float,
            keywords: List[str],
            user_doc
    ) -> str:
        '''Generate constructive feedback based on NLP analysis.'''

        feedback_parts = []

        # Overall assessment
        overall_score = (keyword_score + content_score + completeness_score) / 3

        if overall_score >= 0.8:
            feedback_parts.append("Excellent answer!")
        elif overall_score >= 0.6:
            feedback_parts.append("Good answer with room for improvement.")
        else:
            feedback_parts.append("Answer needs more development.")

        # Keyword coverage feedback
        if keyword_score >= 0.7:
            feedback_parts.append("You covered the key concepts well.")
        elif keyword_score >= 0.5:
            feedback_parts.append("You addressed some key concepts but missed others.")
        else:
            feedback_parts.append("Important concepts are missing from your answer.")
            if keywords:
                # Find missing keywords
                missing = []
                for keyword in keywords[:3]:
                    keyword_doc = self.nlp(keyword)
                    if user_doc.similarity(keyword_doc) < self.similarity_threshold:
                        missing.append(keyword)
                if missing:
                    feedback_parts.append(f"Consider including: {', '.join(missing)}.")

        # Content similarity feedback
        if content_score >= 0.7:
            feedback_parts.append("Your answer aligns well with the expected response.")
        elif content_score < 0.5:
            feedback_parts.append("Your answer differs significantly from the expected response.")

        # Completeness feedback
        if completeness_score >= 0.7:
            feedback_parts.append("Answer is well-detailed and complete.")
        elif completeness_score < 0.5:
            feedback_parts.append("Answer lacks sufficient detail and completeness.")

        return " ".join(feedback_parts)