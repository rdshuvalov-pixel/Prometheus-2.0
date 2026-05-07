-- Profile documents: one CV + up to 3 additional materials per profile.

do $$
begin
  if not exists (select 1 from pg_type where typname = 'profile_document_kind') then
    create type profile_document_kind as enum ('cv', 'description');
  end if;
end $$;

create table if not exists profile_documents (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references candidate_profiles(id) on delete cascade,
  kind profile_document_kind not null,
  file_name text not null,
  storage_path text not null,
  mime_type text,
  byte_size integer,
  extracted_text text,
  uploaded_at timestamptz not null default now()
);

create unique index if not exists profile_documents_one_cv
  on profile_documents(profile_id)
  where kind = 'cv';

create index if not exists profile_documents_profile_kind_uploaded
  on profile_documents(profile_id, kind, uploaded_at desc);

alter table profile_documents enable row level security;

drop policy if exists profile_documents_owner on profile_documents;
create policy profile_documents_owner on profile_documents
  for all
  using (
    exists (
      select 1 from candidate_profiles cp
      where cp.id = profile_documents.profile_id and cp.user_id = auth.uid()
    )
  );

-- Storage bucket + policy (private bucket).
insert into storage.buckets (id, name, public)
values ('profile-docs', 'profile-docs', false)
on conflict (id) do nothing;

drop policy if exists "owner can manage own docs in storage" on storage.objects;
create policy "owner can manage own docs in storage"
on storage.objects for all to authenticated
using (
  bucket_id = 'profile-docs'
  and exists (
    select 1
    from candidate_profiles cp
    where cp.user_id = auth.uid()
      and (storage.foldername(name))[1] = cp.id::text
  )
);
