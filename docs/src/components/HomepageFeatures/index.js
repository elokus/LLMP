import React from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'High-Level Prompt Management',
    Svg: require('@site/static/img/prompt_funnel.svg').default,
    description: (
      <>
          Simplifies prompt creation, storage, and optimization. Enhanced by StructGenie, LLMP prioritizes dependable,
          YAML-formatted outputs that synergize well with large language models.
      </>
    ),
  },
  {
    title: 'Efficiency & Structured Outputs',
    Svg: require('@site/static/img/task_efficiency.svg').default,
    description: (
      <>
        The Program class revolutionizes task initialization, ensuring prompt crafting is straightforward.
          Emphasis on the YAML format guarantees outputs that are both structured and model-friendly.
      </>
    ),
  },
  {
    title: 'Dynamic Management & Optimization',
    Svg: require('@site/static/img/management_optimization.svg').default,
    description: (
      <>
        LLMP stands out with its dedicated optimization system. Adaptable to advanced output rules and committed to ongoing refinement,
          it's a leading solution in the generative NLP domain.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
