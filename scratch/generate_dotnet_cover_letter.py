import shutil
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parent.parent / "generated_resumes"
TEMPLATE = ROOT / "TarunMannava_SoftwareDeveloper_CoverLetter.docx"
OUTPUT = ROOT / "TarunMannava_DotnetDeveloper_CoverLetter.docx"

BODY = [
    "I am excited to apply for this .NET Developer position because I enjoy building backend systems that are reliable, "
    "maintainable, and fast under real traffic. What interests me about this role is the opportunity to work on C# and "
    "ASP.NET Core services that sit at the center of the business, where clean API design, efficient data access, and "
    "performance all matter.",

    "At Cognizant, I spent over two years developing C# and ASP.NET Core microservices on .NET 6 and 8 for a healthcare "
    "insurance platform, handling policy onboarding and validation at more than 20,000 requests per hour at peak. Much of "
    "that work focused on performance. I eliminated N+1 query patterns with batched LINQ queries, Entity Framework Core "
    "eager loading, and composite indexes, added Redis distributed caching to move read traffic off SQL Server, and "
    "parallelized validation workflows with async/await and Task.WhenAll. I also consolidated duplicated business logic "
    "across more than eight microservices into shared service-layer components, secured endpoints with OAuth2 and JWT, "
    "and raised backend test coverage to 70% with xUnit and Moq.",

    "More recently, as a Graduate Research Assistant at the University of South Florida, I prototyped a behavioral health "
    "workflow platform built on .NET 8 microservices, Entity Framework Core, and PostgreSQL, with React and TypeScript "
    "dashboards for utilization reporting. That project gave me experience owning a system end to end, from modeling "
    "session lifecycles and role-based access to building the reporting and test suites around them.",

    "I also bring hands-on experience with Azure, AWS, Docker, and CI/CD, and I use AI developer tools to build and test "
    "software faster while keeping validation and code review in the loop. I enjoy learning how an existing system works, "
    "understanding the problem it is solving, and then figuring out where I can contribute.",

    "I would be excited to bring my .NET backend experience, focus on performance, and willingness to learn to your team. "
    "Thank you for your consideration, and I look forward to the opportunity to speak with you.",
]


def set_paragraph_text(paragraph, text: str) -> None:
    runs = paragraph.runs
    runs[0].text = text
    for run in runs[1:]:
        run.text = ""


def main() -> None:
    shutil.copyfile(TEMPLATE, OUTPUT)
    document = docx.Document(OUTPUT)
    body_paragraphs = [p for p in document.paragraphs if p.text.strip()][2:-1]
    if len(body_paragraphs) != len(BODY):
        raise SystemExit(f"Template has {len(body_paragraphs)} body paragraphs, expected {len(BODY)}")
    for paragraph, text in zip(body_paragraphs, BODY):
        set_paragraph_text(paragraph, text)
    document.save(OUTPUT)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
