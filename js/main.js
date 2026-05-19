// DOM 요소 참조
const menuToggle = document.querySelector('.menu-toggle');
const primaryNav = document.querySelector('.primary-nav');
const topButton = document.querySelector('#top-button');
const siteHeader = document.querySelector('.site-header');
const themeToggle = document.querySelector('.theme-toggle');
const contactForm = document.querySelector('#contact-form');
const reloadProjectsButton = document.querySelector('#reload-projects');
const retryProjectsButton = document.querySelector('#retry-projects');
const projectGrid = document.querySelector('#project-grid');
const projectFilters = document.querySelector('#project-filters');
const projectsFeedback = document.querySelector('#projects-feedback');
const projectsEmpty = document.querySelector('#projects-empty');
const projectsError = document.querySelector('#projects-error');
const typingText = document.querySelector('#typing-text');

// 프로젝트 전역 설정
const GITHUB_USERNAME = 'myy-dev';
const STORAGE_THEME_KEY = 'portfolio-theme';
const TYPING_MESSAGES = [
  '프론트엔드 개발자',
  '사용자 경험 중심 구현',
  '반응형 UI 개발',
];

let allRepos = [];
let selectedLanguage = 'ALL';

// 모바일 메뉴 열기/닫기 및 메뉴 클릭 시 닫기
if (menuToggle && primaryNav) {
  menuToggle.addEventListener('click', () => {
    const isOpen = primaryNav.classList.toggle('is-open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  primaryNav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      primaryNav.classList.remove('is-open');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });
}

// 선택한 테마를 HTML 속성과 localStorage에 반영
const setTheme = (theme) => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_THEME_KEY, theme);

  if (themeToggle) {
    themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
    themeToggle.setAttribute(
      'aria-label',
      theme === 'dark' ? '라이트 모드 전환' : '다크 모드 전환',
    );
  }
};

// 저장된 테마가 있으면 사용하고, 없으면 OS 설정을 기준으로 초기화
const initTheme = () => {
  const savedTheme = localStorage.getItem(STORAGE_THEME_KEY);
  const preferDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme || (preferDark ? 'dark' : 'light');
  setTheme(initialTheme);
};

// 현재 테마를 기준으로 다크/라이트 모드 전환
const toggleTheme = () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  setTheme(currentTheme === 'dark' ? 'light' : 'dark');
};

// 스크롤 위치에 따라 헤더 그림자와 맨 위 버튼 표시 상태 변경
const handleScrollUi = () => {
  const y = window.scrollY;

  if (topButton) {
    topButton.classList.toggle('visible', y >= 300);
  }

  if (siteHeader) {
    siteHeader.classList.toggle('scrolled', y >= 60);
  }
};

// 이메일 형식 정규식
const emailRegExp = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// 지정한 시간만큼 비동기 흐름 지연
const delay = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

// 입력 필드별 에러 메시지 표시
const setFieldError = (inputId, message) => {
  const errorElement = document.querySelector(`#${inputId}-error`);

  if (errorElement) {
    errorElement.textContent = message;
  }
};

// 연락 폼 입력값 검증 후 필드별 에러 객체 반환
const validateForm = (formData) => {
  const errors = {};

  if (!formData.name.trim()) {
    errors.name = '이름 입력 필요';
  }

  if (!formData.email.trim()) {
    errors.email = '이메일 입력 필요';
  } else if (!emailRegExp.test(formData.email.trim())) {
    errors.email = '이메일 형식 확인 필요';
  }

  if (!formData.message.trim()) {
    errors.message = '메시지 입력 필요';
  }

  return errors;
};

// 프로젝트 목록의 로딩/빈 상태/에러 상태 UI 반영
const setProjectsState = (state, message = '') => {
  if (!projectGrid || !projectsFeedback || !projectsEmpty || !projectsError) {
    return;
  }

  projectsFeedback.textContent = message;
  projectsEmpty.hidden = state !== 'empty';
  projectsError.hidden = state !== 'error';

  if (state !== 'success') {
    projectGrid.innerHTML = '';
  }
};

// GitHub 저장소 데이터를 프로젝트 카드 DOM으로 변환
const createProjectCard = (repo) => {
  const card = document.createElement('article');
  card.className = 'project-card reveal';
  card.innerHTML = `
    <h3>${repo.name}</h3>
    <a href="${repo.html_url}" target="_blank" rel="noopener noreferrer">GitHub 보기</a>
  `;
  return card;
};

// 저장소 언어 목록으로 필터 버튼 생성
const renderFilterButtons = (repos) => {
  if (!projectFilters) return;

  const languages = [
    'ALL',
    ...new Set(
      repos
        .map((repo) => repo.language)
        .filter((language) => typeof language === 'string' && language.trim()),
    ),
  ];

  projectFilters.innerHTML = '';
  languages.forEach((language) => {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'filter-button';
    button.textContent = language;
    button.dataset.language = language;

    if (language === selectedLanguage) {
      button.classList.add('active');
    }

    button.addEventListener('click', () => {
      selectedLanguage = language;
      renderProjectsByLanguage();
    });

    projectFilters.appendChild(button);
  });
};

// 선택한 언어 필터에 맞춰 프로젝트 목록 렌더링
const renderProjectsByLanguage = () => {
  if (
    !projectGrid ||
    !projectFilters ||
    !projectsFeedback ||
    !projectsEmpty ||
    !projectsError
  ) {
    return;
  }

  const filteredRepos =
    selectedLanguage === 'ALL'
      ? allRepos
      : allRepos.filter((repo) => repo.language === selectedLanguage);

  projectGrid.innerHTML = '';
  filteredRepos.forEach((repo) => {
    projectGrid.appendChild(createProjectCard(repo));
  });

  projectsEmpty.hidden = filteredRepos.length !== 0;
  projectsError.hidden = true;
  projectsFeedback.textContent =
    selectedLanguage === 'ALL'
      ? `성공 상태 (${filteredRepos.length}건)`
      : `성공 상태 (${selectedLanguage}, ${filteredRepos.length}건)`;

  projectFilters.querySelectorAll('.filter-button').forEach((button) => {
    button.classList.toggle(
      'active',
      button.dataset.language === selectedLanguage,
    );
  });

  observeRevealItems();
};

// GitHub API에서 최신 저장소 목록 조회
const fetchProjects = async () => {
  try {
    setProjectsState('loading', '로딩 중...');

    const [response] = await Promise.all([
      fetch(
        `https://api.github.com/users/${GITHUB_USERNAME}/repos?sort=updated&per_page=8`,
      ),
      delay(2000),
    ]);

    if (!response.ok) {
      if (response.status === 403) {
        throw new Error('GitHub API 호출 제한 상태');
      }
      throw new Error('프로젝트 조회 실패');
    }

    const repos = await response.json();
    if (!Array.isArray(repos) || repos.length === 0) {
      setProjectsState('empty', '빈 상태');
      return;
    }

    allRepos = repos.slice(0, 8);
    selectedLanguage = 'ALL';
    renderFilterButtons(allRepos);
    renderProjectsByLanguage();
  } catch (error) {
    setProjectsState('error', error.message);
  }
};

// 화면에 들어온 섹션과 프로젝트 카드에 reveal 애니메이션 적용
const observeRevealItems = () => {
  const revealItems = document.querySelectorAll('.section, .project-card');
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('in-view');
        }
      });
    },
    { threshold: 0.2 },
  );

  revealItems.forEach((item) => {
    item.classList.add('reveal');
    observer.observe(item);
  });
};

// 히어로 영역 소개 문구 타이핑 효과 실행
const startTypingEffect = () => {
  if (!typingText) return;

  let textIndex = 0;
  let charIndex = 0;
  let isDeleting = false;

  const type = () => {
    const currentText = TYPING_MESSAGES[textIndex];

    if (isDeleting) {
      charIndex -= 1;
    } else {
      charIndex += 1;
    }

    typingText.textContent = currentText.slice(0, charIndex);

    let delay = isDeleting ? 50 : 95;
    if (!isDeleting && charIndex === currentText.length) {
      delay = 1100;
      isDeleting = true;
    } else if (isDeleting && charIndex === 0) {
      isDeleting = false;
      textIndex = (textIndex + 1) % TYPING_MESSAGES.length;
      delay = 260;
    }

    setTimeout(type, delay);
  };

  type();
};

// 이벤트 연결
if (themeToggle) {
  themeToggle.addEventListener('click', toggleTheme);
}
// "위로 가기" 버튼 클릭 이벤트(부드럽게 올라가기)
if (topButton) {
  topButton.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

if (contactForm) {
  contactForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = {
      name: contactForm.name.value,
      email: contactForm.email.value,
      message: contactForm.message.value,
    };
    const formSuccess = document.querySelector('#form-success');
    const errors = validateForm(formData);

    setFieldError('name', errors.name || '');
    setFieldError('email', errors.email || '');
    setFieldError('message', errors.message || '');

    if (formSuccess) {
      formSuccess.textContent = '';
    }

    if (Object.keys(errors).length > 0) {
      return;
    }

    const endpoint = contactForm.dataset.formspreeEndpoint || '';
    if (!endpoint || endpoint.includes('your_form_id')) {
      if (formSuccess) {
        formSuccess.textContent = 'Formspree 엔드포인트 설정 필요';
      }
      return;
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('전송 실패');
      }

      if (formSuccess) {
        formSuccess.textContent = '메시지 전송 완료';
      }
      contactForm.reset();
    } catch (error) {
      if (formSuccess) {
        formSuccess.textContent = '메시지 전송 실패, 잠시 후 재시도 필요';
      }
    }
  });
}

if (reloadProjectsButton) {
  reloadProjectsButton.addEventListener('click', fetchProjects);
}

if (retryProjectsButton) {
  retryProjectsButton.addEventListener('click', fetchProjects);
}

window.addEventListener('scroll', handleScrollUi);

// 초기 실행 (index.html의 script 태그에 defer 속성이 있어 DOM 로드 후 1회 자동 실행됨)
initTheme(); // 다크/라이트 테마 초기화
handleScrollUi(); // 스크롤 UI (헤더 스타일, 위로 가기 버튼 등) 초기화
observeRevealItems(); // 스크롤 시 요소들이 나타나는 애니메이션(옵저버) 등록
startTypingEffect(); // 히어로 영역의 직업 소개 타이핑 효과 시작
fetchProjects(); // 깃허브 API를 호출하여 프로젝트 목록 초기 렌더링
