from __future__ import annotations

from como_core.job import Job, JobSearchResult

from .._params import clean_params, require_one_of
from ._base import AsyncResource, SyncResource

_PATH_GET = "/v1/ghost/job"
_PATH_SEARCH = "/v1/ghost/job-search"


def _get_params(*, job_id, url) -> dict[str, str]:
    require_one_of(job_id=job_id, url=url)
    return clean_params({"jobId": job_id, "url": url})


def _search_params(**kwargs) -> dict[str, str]:
    return clean_params(
        {
            "search": kwargs.get("search"),
            "companyId": kwargs.get("company_id"),
            "location": kwargs.get("location"),
            "geoId": kwargs.get("geo_id"),
            "sortBy": kwargs.get("sort_by"),
            "workplaceType": kwargs.get("workplace_type"),
            "employmentType": kwargs.get("employment_type"),
            "salary": kwargs.get("salary"),
            "postedLimit": kwargs.get("posted_limit"),
            "experienceLevel": kwargs.get("experience_level"),
            "industryId": kwargs.get("industry_id"),
            "functionId": kwargs.get("function_id"),
            "under10Applicants": kwargs.get("under10_applicants"),
            "easyApply": kwargs.get("easy_apply"),
            "page": kwargs.get("page"),
        }
    )


class JobResource(SyncResource):
    def get(
        self,
        *,
        job_id: str | None = None,
        url: str | None = None,
    ) -> Job:
        params = _get_params(job_id=job_id, url=url)
        body = self._t.get(_PATH_GET, params=params)
        return Job.model_validate(body.get("element") or {})

    def search(
        self,
        *,
        search: str | None = None,
        company_id: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        sort_by: str | None = None,
        workplace_type: str | None = None,
        employment_type: str | None = None,
        salary: str | None = None,
        posted_limit: str | None = None,
        experience_level: str | None = None,
        industry_id: str | None = None,
        function_id: str | None = None,
        under10_applicants: str | None = None,
        easy_apply: str | None = None,
        page: int | None = None,
    ) -> JobSearchResult:
        params = _search_params(
            search=search,
            company_id=company_id,
            location=location,
            geo_id=geo_id,
            sort_by=sort_by,
            workplace_type=workplace_type,
            employment_type=employment_type,
            salary=salary,
            posted_limit=posted_limit,
            experience_level=experience_level,
            industry_id=industry_id,
            function_id=function_id,
            under10_applicants=under10_applicants,
            easy_apply=easy_apply,
            page=page,
        )
        body = self._t.get(_PATH_SEARCH, params=params)
        return JobSearchResult.model_validate(body)


class AsyncJobResource(AsyncResource):
    async def get(
        self,
        *,
        job_id: str | None = None,
        url: str | None = None,
    ) -> Job:
        params = _get_params(job_id=job_id, url=url)
        body = await self._t.get(_PATH_GET, params=params)
        return Job.model_validate(body.get("element") or {})

    async def search(
        self,
        *,
        search: str | None = None,
        company_id: str | None = None,
        location: str | None = None,
        geo_id: str | None = None,
        sort_by: str | None = None,
        workplace_type: str | None = None,
        employment_type: str | None = None,
        salary: str | None = None,
        posted_limit: str | None = None,
        experience_level: str | None = None,
        industry_id: str | None = None,
        function_id: str | None = None,
        under10_applicants: str | None = None,
        easy_apply: str | None = None,
        page: int | None = None,
    ) -> JobSearchResult:
        params = _search_params(
            search=search,
            company_id=company_id,
            location=location,
            geo_id=geo_id,
            sort_by=sort_by,
            workplace_type=workplace_type,
            employment_type=employment_type,
            salary=salary,
            posted_limit=posted_limit,
            experience_level=experience_level,
            industry_id=industry_id,
            function_id=function_id,
            under10_applicants=under10_applicants,
            easy_apply=easy_apply,
            page=page,
        )
        body = await self._t.get(_PATH_SEARCH, params=params)
        return JobSearchResult.model_validate(body)
