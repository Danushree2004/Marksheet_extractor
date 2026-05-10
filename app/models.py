from typing import Optional, List
from pydantic import BaseModel, Field


# Using Pydantic models to make sure our JSON output always follows the same format.
# This makes it much easier for the frontend to display the data.


class FieldWithConfidence(BaseModel):
    # Every extracted piece of data comes with a confidence score (0.0 to 1.0)
    # This helps us tell the user how sure we are about the value.
    value: Optional[str] = Field(None, description="The actual text we found")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How confident we are in this specific field"
    )
    bounding_box: Optional[List[List[float]]] = Field(
        None,
        description="Coordinates of the text in the image"
    )


class SubjectMarks(BaseModel):
    # Model for a single subject row on the marksheet
    subject: FieldWithConfidence
    max_marks: FieldWithConfidence
    obtained_marks: FieldWithConfidence
    # Not all marksheets show grades
    grade: Optional[FieldWithConfidence] = None


class CandidateDetails(BaseModel):
    # Personal details about the student.
    # I made these Optional because some boards don't show Father's name or DOB.
    name: Optional[FieldWithConfidence] = None
    full_name: Optional[FieldWithConfidence] = None  # Added explicitly
    father_name: Optional[FieldWithConfidence] = None
    mother_name: Optional[FieldWithConfidence] = None
    roll_number: Optional[FieldWithConfidence] = None
    registration_number: Optional[FieldWithConfidence] = None
    # Alternative name for registration_number
    register_number: Optional[FieldWithConfidence] = None
    date_of_birth: Optional[FieldWithConfidence] = None
    exam_year: Optional[FieldWithConfidence] = None
    exam_date: Optional[FieldWithConfidence] = None  # For exam sheets
    board_university: Optional[FieldWithConfidence] = None
    institution: Optional[FieldWithConfidence] = None
    programme: Optional[FieldWithConfidence] = None  # For exam sheets
    course_code: Optional[FieldWithConfidence] = None  # For exam sheets
    course_name: Optional[FieldWithConfidence] = None  # For exam sheets
    branch: Optional[FieldWithConfidence] = None  # For exam sheets
    cat_number: Optional[FieldWithConfidence] = None  # Continuous Assessment Test number


class AcademicDetails(BaseModel):
    # Overall summary and list of subjects
    subjects: List[SubjectMarks] = Field(default_factory=list)
    overall_result: Optional[FieldWithConfidence] = None
    overall_grade: Optional[FieldWithConfidence] = None
    division: Optional[FieldWithConfidence] = None  # E.g. First Division
    issue_date: Optional[FieldWithConfidence] = None
    issue_place: Optional[FieldWithConfidence] = None


# ============= EXAM SHEET MODELS (For Part-A/Part-B Format) =============


class ExamQuestion(BaseModel):
    # Individual question in Part A or Part B
    question_no: FieldWithConfidence
    max_marks: FieldWithConfidence
    obtained_marks: Optional[FieldWithConfidence] = None


class ExamPart(BaseModel):
    # Part A or Part B section
    max_marks: FieldWithConfidence
    obtained_marks: Optional[FieldWithConfidence] = None
    questions: List[ExamQuestion] = Field(default_factory=list)


class ExamTotals(BaseModel):
    # Summary of all totals
    part_a_total: Optional[FieldWithConfidence] = None
    part_b_total: Optional[FieldWithConfidence] = None
    grand_total: Optional[FieldWithConfidence] = None
    max_marks: FieldWithConfidence


class ExamMarks(BaseModel):
    # Wrapper for Part A and Part B
    part_a: Optional[ExamPart] = None
    part_b: Optional[ExamPart] = None


class ExtractionResponse(BaseModel):
    # This is the final JSON object the API returns
    # Now supports both traditional marksheets and exam sheets with Part A/B
    candidate_details: CandidateDetails
    academic_details: Optional[AcademicDetails] = None  # For traditional
    exam_marks: Optional[ExamMarks] = None  # For exam sheets with Part A/B
    exam_totals: Optional[ExamTotals] = None  # For exam sheets with Part A/B
    overall_confidence: float = Field(..., ge=0.0, le=1.0)

    # Adding an example so developers can see what to expect in Swagger
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_details": {
                    "name": {"value": "MAYANK SAHU", "confidence": 0.98},
                    "roll_number": {"value": "2023001", "confidence": 1.0}
                },
                "academic_details": {
                    "subjects": [
                        {
                            "subject": {
                                "value": "Physics",
                                "confidence": 0.95
                            },
                            "obtained_marks": {
                                "value": "88",
                                "confidence": 0.98
                            },
                            "max_marks": {
                                "value": "100",
                                "confidence": 1.0
                            }
                        }
                    ],
                    "overall_result": {"value": "PASS", "confidence": 0.99}
                },
                "overall_confidence": 0.96
            }
        }


class ErrorResponse(BaseModel):
    # To keep error messages consistent
    error: str
    detail: Optional[str] = None


class ExamSheetResponse(BaseModel):
    # Response for exam answer sheets with Part A and Part B
    candidate_details: CandidateDetails
    exam_marks: Optional[ExamMarks] = None
    exam_totals: Optional[ExamTotals] = None
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
