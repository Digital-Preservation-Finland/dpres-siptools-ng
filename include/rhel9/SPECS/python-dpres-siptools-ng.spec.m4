# vim:ft=spec

%define file_prefix M4_FILE_PREFIX
%define file_ext M4_FILE_EXT
%define file_version M4_FILE_VERSION
%define file_release_tag %{nil}M4_FILE_RELEASE_TAG
%define file_release_number M4_FILE_RELEASE_NUMBER
%define file_build_number M4_FILE_BUILD_NUMBER
%define file_commit_ref M4_FILE_COMMIT_REF

Name:           python-dpres-siptools-ng
Version:        %{file_version}
Release:        %{file_release_number}%{file_release_tag}.%{file_build_number}.git%{file_commit_ref}%{?dist}
Summary:        Library for creating Submission Information Packages (SIP) that comply to the specifications of national digital preservation services of Finland.
License:        LGPLv3+
URL:            https://www.digitalpreservation.fi
Source0:        %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}.%{file_ext}
BuildArch:      noarch

BuildRequires:  python3-pytest
BuildRequires:  python3-setuptools_scm
BuildRequires:  python3-devel
BuildRequires:  pyproject-rpm-macros
BuildRequires:  %{py3_dist pip}
BuildRequires:  %{py3_dist setuptools}
BuildRequires:  %{py3_dist wheel}

%global _description %{expand:
Library for creating Submission Information Packages (SIP) that comply to the specifications of national digital preservation services of Finland.
}

%description %_description

%package -n python3-dpres-siptools-ng
Summary: %{summary}
Requires:       %{py3_dist dpres-mets-builder}
Requires:       python3-file-scraper-full
Requires:       %{py3_dist dpres-signature}
%description -n python3-dpres-siptools-ng %_description

%prep
%autosetup -n %{file_prefix}-v%{file_version}%{?file_release_tag}-%{file_build_number}-g%{file_commit_ref}

%build
export SETUPTOOLS_SCM_PRETEND_VERSION=%{file_version}
%pyproject_wheel

%install
%pyproject_install
%pyproject_save_files siptools_ng

%files -n python3-dpres-siptools-ng -f %{pyproject_files}
%doc README.rst

# TODO: For now changelog must be last, because it is generated automatically
# from git log command. Appending should be fixed to happen only after %changelog macro
%changelog
